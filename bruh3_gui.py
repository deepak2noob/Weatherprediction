import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry

# --- City Coordinates Map ---
city_coords = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Bangalore": (12.9716, 77.5946)
}

# --- GUI Setup ---
root = tk.Tk()
root.title("India Weather Predictor (2025)")
root.geometry("430x350")
root.configure(bg="#f0f2f5")

tk.Label(root, text="🌤️ Weather Predictor", font=("Helvetica", 16, "bold"), bg="#f0f2f5", fg="#333").pack(pady=10)

frame = tk.Frame(root, bg="#f0f2f5")
frame.pack(pady=5)

tk.Label(frame, text="City:", font=("Helvetica", 12), bg="#f0f2f5").grid(row=0, column=0, padx=5, sticky="e")
city_var = tk.StringVar(value="Delhi")
city_menu = tk.OptionMenu(frame, city_var, *city_coords.keys())
city_menu.config(font=("Helvetica", 11), bg="#e0e0e0")
city_menu.grid(row=0, column=1)

tk.Label(frame, text="Date (2025):", font=("Helvetica", 12), bg="#f0f2f5").grid(row=1, column=0, padx=5, pady=10, sticky="e")
date_entry = DateEntry(frame, width=16, year=2025, mindate=datetime(2025,1,1), maxdate=datetime(2025,12,31), date_pattern='yyyy-mm-dd', font=("Helvetica", 11))
date_entry.grid(row=1, column=1)

status_label = tk.Label(root, text="", font=("Helvetica", 10), fg="gray", bg="#f0f2f5")
status_label.pack(pady=5)

def fetch_and_predict():
    selected_city = city_var.get()
    lat, lon = city_coords[selected_city]
    date_str = date_entry.get()

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        if target_date.year != 2025:
            raise ValueError("Date must be in 2025.")
    except Exception as e:
        messagebox.showerror("Invalid Date", f"{str(e)}")
        return

    # Loading popup
    loading_popup = tk.Toplevel(root)
    loading_popup.title("Loading")
    loading_popup.geometry("250x80")
    loading_popup.resizable(False, False)
    tk.Label(loading_popup, text="Fetching data...\nPlease wait.", font=("Helvetica", 11)).pack(pady=15)
    loading_popup.grab_set()
    root.update()

    all_years_data = []
    for year in range(2014, 2025):
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "daily": "temperature_2m_mean",
            "timezone": "Asia/Kolkata"
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch data for {year}")
            continue
        year_data = response.json()
        df = pd.DataFrame({
            "date": pd.to_datetime(year_data["daily"]["time"]),
            "temperature": year_data["daily"]["temperature_2m_mean"]
        })
        all_years_data.append(df)

    if not all_years_data:
        loading_popup.destroy()
        messagebox.showerror("Error", "Could not fetch any weather data.")
        return

    df_all = pd.concat(all_years_data).sort_values("date").reset_index(drop=True)
    loading_popup.destroy()

    df_all["month"] = df_all["date"].dt.month
    df_all["day"] = df_all["date"].dt.day

    target_month = target_date.month
    target_day = target_date.day
    matching_days = df_all[(df_all["month"] == target_month) & (df_all["day"] == target_day)]

    if matching_days.empty:
        messagebox.showinfo("No Data", "No historical data found for this date.")
        return

    # Outlier handling using IQR
    temps = matching_days["temperature"]
    Q1 = temps.quantile(0.25)
    Q3 = temps.quantile(0.75)
    IQR = Q3 - Q1
    filtered = temps[(temps >= Q1 - 1.5 * IQR) & (temps <= Q3 + 1.5 * IQR)]
    predicted_temp = filtered.mean()

    # Summary statistics
    print("\n--- Summary Statistics ---")
    print(f"Historical values on {target_day:02d}-{target_month:02d} (2014–2024):")
    print(f"Min: {temps.min():.2f}°C")
    print(f"Max: {temps.max():.2f}°C")
    print(f"Mean (raw): {temps.mean():.2f}°C")
    print(f"Mean (IQR filtered): {predicted_temp:.2f}°C")
    print(f"Std Dev: {temps.std():.2f}°C")
    status_label.config(text="✅ Prediction complete.")

    df_all["year"] = df_all["date"].dt.year
    df_all["day_of_year"] = df_all["date"].dt.dayofyear

    plt.figure(figsize=(14, 7))

    for year in df_all["year"].unique():
        yearly_data = df_all[df_all["year"] == year]
        plt.plot(
            yearly_data["day_of_year"],
            yearly_data["temperature"],
            label=str(year)
        )

    prediction_day = target_date.timetuple().tm_yday
    plt.axvline(x=prediction_day, color='black', linestyle='--', label="Prediction Date")

    # Highlighted prediction box (only predicted temp)
    plt.text(
        360,
        min(df_all["temperature"]) + 1,
        f"{selected_city} - Predicted Temp\n({target_date.date()}): {predicted_temp:.2f}°C",
        fontsize=12,
        fontweight="bold",
        color="black",
        ha="right",
        bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.5")
    )

    # Subtle min/max info below the plot
    plt.figtext(
        0.5, -0.05,
        f"Min: {temps.min():.1f}°C, Max: {temps.max():.1f}°C",
        ha="center",
        fontsize=9,
        fontweight="normal",
        color="gray"
    )

    plt.xlabel("Day of Year (1 = Jan 1, 365 = Dec 31)")
    plt.ylabel("Temperature (°C)")
    plt.title(f"{selected_city} Temperature Trends: 2014–2024")
    plt.legend(title="Year")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- Buttons ---
button_frame = tk.Frame(root, bg="#f0f2f5")
button_frame.pack(pady=10)

tk.Button(button_frame, text="Predict Temperature", font=("Helvetica", 11), bg="#4CAF50", fg="white", padx=10, command=fetch_and_predict).grid(row=0, column=0, padx=10)
tk.Button(button_frame, text="Exit", font=("Helvetica", 11), bg="#f44336", fg="white", padx=10, command=root.destroy).grid(row=0, column=1, padx=10)

# --- Run GUI ---
root.mainloop()
