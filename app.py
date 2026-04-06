import pyodbc
import pandas as pd
from flask import Flask, request, jsonify
import pickle
import pyodbc
import pandas as pd

app = Flask(__name__)

def get_latest_train_data(train_no, stop_seq):
    conn = pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=(localdb)\MSSQLLocalDB;DATABASE=RailwayDB;Trusted_Connection=yes;"
    )

    query = """
    SELECT TOP 1 *
    FROM train_data
    WHERE train_no = ? AND stop_seq = ?
    ORDER BY Date DESC
    """

    df = pd.read_sql(query, conn, params=[train_no, stop_seq])
    conn.close()

    return df

@app.route("/")
def home():
    return "Flask is working!"

arrival_model = pickle.load(open("arrival_model.pkl", "rb"))
departure_model = pickle.load(open("departure_model.pkl", "rb"))

station_encoder = pickle.load(open("station_encoder.pkl", "rb"))
weather_encoder = pickle.load(open("weather_encoder.pkl", "rb"))

def time_to_minutes(t):
    try:
        h, m, s = map(int, t.split(":"))
        return h * 60 + m
    except:
        return 0

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    df = get_latest_train_data(data["train_no"], data["stop_seq"])

    if df.empty:
        return jsonify({"error": "No data found"}), 404

    row = df.iloc[0]

    try:
        station = station_encoder.transform([row["station"]])[0]
        weather = weather_encoder.transform([row["weather"]])[0]
    except:
        return jsonify({"error": "Encoding error"}), 400

    prev_delay = 0 if row["stop_seq"] == 1 else row["arr_delay"]

    input_data = [[
        row["train_no"],
        row["stop_seq"],
        station,
        row["distance_from_src"],
        time_to_minutes(row["sched_arr"]),
        time_to_minutes(row["sched_dep"]),
        row["peak_hour"],
        row["holiday_flag"],
        weather,
        prev_delay
    ]]

    arrival_prediction = arrival_model.predict(input_data)[0]
    departure_prediction = departure_model.predict(input_data)[0]

    return jsonify({
        "predicted_arrival_delay": round(float(arrival_prediction), 2),
        "predicted_departure_delay": round(float(departure_prediction), 2)
    })

if __name__ == "__main__":
    app.run(debug=True)