import pandas as pd

import requests
import datetime

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
        return None


# Sensors and date range
sensors = [
    "sensor.aqara_bh2_on_wall_temperature_2",
    "sensor.aqara_bh1_outside_temperature",
    "sensor.sp26_energy_power",
]
start_date = datetime.datetime(2024, 12, 25, 1, 13)  # Replace with your start date
end_date = datetime.datetime(2024, 12, 25, 13, 30)  # Replace with your end date

# Fetch and process data
for sensor in sensors:
    data = get_sensor_data(sensor, start_date.isoformat(), end_date.isoformat())
    if data:
        print(f"Data for {sensor}:")
        for entry in data:
            print(entry)
            for rec in entry:
                print(f"{rec['last_updated']} {rec['state']}")
