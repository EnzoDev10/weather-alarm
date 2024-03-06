import openmeteo_requests

import requests_cache
from retry_requests import retry

import pandas as pd
import datetime as dt
from tabulate import tabulate


# Setup the Open-meteo API client with cache and retry error
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": -34.6131,
    "longitude": -58.3772,
    "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
}

responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]

daily = response.Daily()
daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy().tolist()
daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy().tolist()
daily_precipitation_sum = daily.Variables(2).ValuesAsNumpy().tolist()


# Rounds the values of a list to 1 decimal place
def rounder(list, int=1):
    try:
        rounded_list = [round(elem, int) for elem in list]
        return rounded_list
    except TypeError:
        return list


daily_data = {
    "date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left",
    )
}

# Weekday gives an int to each date dpeneding on the day.  monday = 0
# Sunday = 6. the map changes the int to then name equivalent
daily_data["days"] = daily_data["date"].weekday.map(
    {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "saturday",
        6: "Sunday",
    }
)


daily_data["temp_max"] = rounder(daily_temperature_2m_max)
daily_data["temp_min"] = rounder(daily_temperature_2m_min)
daily_data["precipitation"] = rounder(daily_precipitation_sum, 0)


daily_dataframe = pd.DataFrame(data=daily_data)

daily_dataframe["date"] = daily_dataframe["date"].dt.date

print(tabulate(daily_dataframe, headers="keys", tablefmt="grid"))

# TODO
# 2 Detect if a precipitation value is above 25-50%.
# 3 know the day in which that will happen.
# 4 Assign both values to variables.
# 5 Create a message template to notify about the values.
# 6 Create a message template for the days when there is not rain.
# 7 send an email each morning with one of the two messages.
