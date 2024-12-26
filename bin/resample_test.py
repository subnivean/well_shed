import requests
import datetime
import pandas as pd

# Home Assistant API settings
base_url = "https://honeyhill1.duckdns.org:14760"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3N2ZkYWQ3YTgxM2Y0ZDAzOTlkNGVjM2ZjYjVlZjVjNyIsImlhdCI6MTczNDcyOTU2OSwiZXhwIjoyMDUwMDg5NTY5fQ.clB5tyKFDWQ4G3s0CRIeJ0aTzFyIkC_9zcyI0wSG860"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}


# Function to get historical data for a sensor
def get_sensor_data(sensor_id, start_time, end_time):
    url = f"{base_url}/api/history/period/{start_time}"
    params = {
        "filter_entity_id": sensor_id,
        "end_time": end_time,
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Failed to fetch data for {sensor_id}: {response.status_code}, {response.text}"
        )
        return []


# Fetch and process data into a DataFrame
def fetch_sensor_data(sensor_id, start_date, end_date):
    data = get_sensor_data(sensor_id, start_date.isoformat(), end_date.isoformat())
    if not data:
        return pd.DataFrame()

    # Transform JSON data into a DataFrame
    records = []
    for state in data[0][1:]:  # Each sensor returns a list of states

        # Convert switch states from text to numeric
        if state["state"] == "on":
            state["state"] = "1"
        elif state["state"] == "off":
            state["state"] = "0"
        else:
            pass

        records.append(
            {
                "time": state["last_changed"],
                "state": (
                    float(state["state"])
                    if state["state"].replace(".", "", 1).isdigit()
                    else None
                ),
            }
        )
    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M:%S.%f%z")
    df.set_index("time", inplace=True)  # Set datetime as index
    return df


# Resample data to standard intervals
def resample_sensor_data(df, frequency="1min"):
    return (
        df.resample(
            frequency,
        )
        .mean()
        .interpolate()
    )  # Adjust this method as needed (e.g., interpolate)


# Parameters
sensors = [
    "sensor.aqara_bh2_on_wall_temperature_2",
    "sensor.aqara_bh1_outside_temperature",
    "switch.sp26",
    # "sensor.sp26_energy_total",
    # "sensor.sp26_energy_power",
]
start_date = datetime.datetime(2024, 12, 26, 1, 20)  # Replace with your start date
end_date = datetime.datetime(2024, 12, 26, 11, 30)  # Replace with your end date

# Fetch and process data for each sensor
for sensor in sensors:
    raw_df = fetch_sensor_data(sensor, start_date, end_date)
    if not "switch." in sensor and not raw_df.empty:
        resampled_df = resample_sensor_data(raw_df)
        print(f"Resampled data for {sensor}:")
        print(resampled_df)
    elif "switch." in sensor:
        pass
    else:
        print(f"No data available for {sensor}")

if "switch." in sensor:
    df = raw_df
    # Ensure the time index is in datetime format
    df["time"] = pd.to_datetime(df.index)

    # Calculate the duration between consecutive timestamps
    df["duration"] = df["time"].diff().dt.total_seconds()

    # Shift the state column to associate the duration with the previous state
    df["previous_state"] = df["state"].shift()

    # Drop the first row where duration is NaN
    df = df.dropna(subset=["duration"])

    if df.iloc[-1]["state"] == 0.0:
        df = df.iloc[:-1]  # Drop the last row

    start_date, end_date = df.index[0], df.index[-1]

    # Group by the previous state and sum the durations
    state_durations = df.groupby("previous_state")["duration"].sum()

    print(state_durations)
    print()
    print(
        f"Equivalent steady-state power: {int(state_durations[1] / (state_durations.sum()) * 675):d} watts"
    )

    meantemp = resampled_df.loc[start_date:end_date].mean()

    print(f"Mean temperature: {float(meantemp.iloc[0]):4.1f}")
