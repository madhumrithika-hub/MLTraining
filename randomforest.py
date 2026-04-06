from flask import Flask, request, jsonify
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle
import os

app = Flask(__name__)

MODEL_FILE = "model.pkl"
ENCODER_FILE = "encoders.pkl"

model = None
encoders = {}

def convert_hour(time_str):
    try:
        return int(str(time_str).split(":")[0])
    except:
        print("ERROR in convert_hour with value:", time_str)
        return 0

@app.route("/train", methods=["GET"])
def train():
    global model, encoders

    df = pd.read_csv("we.csv")
    df = df.dropna()

    df["Start_hour"] = df["Start_hour"].apply(convert_hour)
    df["End_hour"] = df["End_hour"].apply(convert_hour)

    le = LabelEncoder()
    df["day_name"] = le.fit_transform(df["day_name"])
    encoders["day_name"] = le

    X = df[["date", "month", "year", "day_name", "Start_hour", "End_hour"]]

    y = df[["temp", "hum"]]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)

    pickle.dump(model, open(MODEL_FILE, "wb"))
    pickle.dump(encoders, open(ENCODER_FILE, "wb"))

    return jsonify({
        "message": "Regression model trained!",
        "R2_score": round(score, 3)
    })

@app.route("/predict", methods=["GET", "POST"])
def predict():
    print("NEW CODE IS RUNNING")
    global model, encoders

    if request.method == "GET":
        return "Use POST request with JSON data"

    elif request.method == "POST":
        try:
            if model is None:
                model = pickle.load(open("model.pkl", "rb"))
                encoders = pickle.load(open("encoders.pkl", "rb"))
                
            data = request.get_json()
            
            input_df = pd.DataFrame([{
                "date": data["date"],
                "month": data["month"],
                "year": data["year"],
                "day_name": data["day_name"],
                "Start_hour": data["Start_hour"],
                "End_hour": data["End_hour"]
                }])
            
            print("RAW INPUT:")
            print(input_df)
            
            input_df["Start_hour"] = input_df["Start_hour"].apply(convert_hour)
            
            input_df["End_hour"] = input_df["End_hour"].apply(convert_hour)
            
            input_df["day_name"] = encoders["day_name"].transform(input_df["day_name"])

            print(input_df)
            print(input_df.dtypes)
            
            prediction = model.predict(input_df)
            
            return jsonify({
                 "predicted_temperature": round(prediction[0][0], 2),
                 "predicted_humidity": round(prediction[0][1], 2)
           })
        
        except Exception as e:
            return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)