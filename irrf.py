import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle


train_df = pd.read_csv("Railway_Delay_Feb_2026.csv")
test_df = pd.read_csv("Railway_Delay_Mar_2026.csv")

df = pd.concat([train_df, test_df], axis=0)

df["Date"] = pd.to_datetime(df["Date"])

df = df.sort_values(by=["Date", "train_no", "stop_seq"])


def time_to_minutes(t):
    try:
        h, m, s = map(int, str(t).split(":"))
        return h * 60 + m
    except:
        return 0


for col in ["sched_arr", "actual_arr", "sched_dep", "actual_dep"]:
    df[col] = df[col].apply(time_to_minutes)

station_encoder = LabelEncoder()
weather_encoder = LabelEncoder()

df["station"] = station_encoder.fit_transform(df["station"])
df["weather"] = weather_encoder.fit_transform(df["weather"])

pickle.dump(station_encoder, open("station_encoder.pkl", "wb"))
pickle.dump(weather_encoder, open("weather_encoder.pkl", "wb"))

df["prev_arr_delay"] = df.groupby("trip_id")["arr_delay"].shift(1)
df["prev_arr_delay"] = df["prev_arr_delay"].fillna(0)

train_df = df.iloc[:len(train_df)]
test_df = df.iloc[len(train_df):]

features = [
    "train_no",
    "stop_seq",
    "station",
    "distance_from_src",
    "sched_arr",
    "sched_dep",
    "peak_hour",
    "holiday_flag",
    "weather",
    "prev_arr_delay"
]

X_train = train_df[features]
X_test = test_df[features]

y_arr_train = train_df["arr_delay"]
y_dep_train = train_df["dep_delay"]

arrival_model = RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42)
departure_model = RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42)

arrival_model.fit(X_train, y_arr_train)
departure_model.fit(X_train, y_dep_train)

pickle.dump(arrival_model, open("arrival_model.pkl", "wb"))
pickle.dump(departure_model, open("departure_model.pkl", "wb"))

print("Models trained successfully!")