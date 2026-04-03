import pandas as pd
import pyodbc

print(pyodbc.drivers())

feb_df = pd.read_csv("Railway_Delay_Feb_2026.csv")
march_df = pd.read_csv("Railway_Delay_Mar_2026.csv")

df = pd.concat([feb_df, march_df], ignore_index=True)

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=(localdb)\MSSQLLocalDB;DATABASE=RailwayDB;Trusted_Connection=yes;"
)

cursor = conn.cursor()

for index, row in df.iterrows():
    cursor.execute("""
        INSERT INTO train_data (
            trip_id, Date, train_no, stop_seq, station,
            distance_from_src, sched_arr, actual_arr,
            sched_dep, actual_dep, peak_hour,
            holiday_flag, weather, dep_delay, arr_delay
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    str(row["trip_id"]),
    row["Date"],
    int(row["train_no"]),
    int(row["stop_seq"]),
    str(row["station"]),
    float(row["distance_from_src"]),
    str(row["sched_arr"]),
    str(row["actual_arr"]),
    str(row["sched_dep"]),
    str(row["actual_dep"]),
    int(row["peak_hour"]),
    int(row["holiday_flag"]),
    str(row["weather"]),
    float(row["dep_delay"]),
    float(row["arr_delay"])
    )

conn.commit()
conn.close()

print("Data inserted successfully!")
