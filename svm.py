from flask import Flask, request, jsonify
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVR
from sklearn.multioutput import MultiOutputRegressor
import pickle

app = Flask(__name__)

model = None
encoder = None
scaler = None

def convert_hour(time_str):
    return int(str(time_str).split(":")[0])

@app.route("/train", methods=["GET"])
def train():
    global model, encoder, scaler

    df = pd.read_csv("we.csv")
    df = df.dropna()

    df["Start_hour"] = df["Start_hour"].apply(convert_hour)
    df["End_hour"] = df["End_hour"].apply(convert_hour)

    encoder = LabelEncoder()
    df["day_name"] = encoder.fit_transform(df["day_name"])

    print("Day Name Encoding Mapping:")
    print(dict(zip(encoder.classes_, encoder.transform(encoder.classes_))))

    X = df[["date", "month", "year", "day_name", "Start_hour", "End_hour"]]

    y = df[["temp", "hum"]]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42
    )

    model = MultiOutputRegressor(SVR(kernel="rbf"))
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)

    pickle.dump(model, open("model.pkl", "wb"))
    pickle.dump(encoder, open("encoder.pkl", "wb"))
    pickle.dump(scaler, open("scaler.pkl", "wb"))

    return jsonify({
        "message": "SVM Regression model trained!",
        "R2_score": round(score, 3)
    })


@app.route("/predict", methods=["POST"])
def predict():
    global model, encoder, scaler

    try:
        if model is None:
            model = pickle.load(open("model.pkl", "rb"))
            encoder = pickle.load(open("encoder.pkl", "rb"))
            scaler = pickle.load(open("scaler.pkl", "rb"))

        data = request.get_json()

        input_df = pd.DataFrame([{
            "date": int(data["date"]),
            "month": int(data["month"]),
            "year": int(data["year"]),
            "day_name": int(data["day_name"]),
            "Start_hour": convert_hour(data["Start_hour"]),
            "End_hour": convert_hour(data["End_hour"])
        }])

        #input_df["day_name"] = encoder.transform(input_df["day_name"])

        input_scaled = scaler.transform(input_df)

        prediction = model.predict(input_scaled)

        return jsonify({
            "predicted_temperature": round(prediction[0][0], 2),
            "predicted_humidity": round(prediction[0][1], 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)