import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load data
members = pd.read_excel("members.xlsx")
attendance = pd.read_excel("attendance.xlsx")

# Rename columns
members.rename(columns={
    "Number": "PhoneNumber",
    "Start Date": "StartDate",
    "End Date": "EndDate",
    "Plan Name": "PlanName",
    "Plan Status": "PlanStatus",
    "Net Amount": "NetAmount",
    "Received Amount": "ReceivedAmount"
}, inplace=True)

attendance.rename(columns={
    "Mobile Number": "PhoneNumber",
    "Checkin Time": "CheckinTime"
}, inplace=True)

# Date conversion
members["StartDate"] = pd.to_datetime(members["StartDate"], errors="coerce")
members["EndDate"] = pd.to_datetime(members["EndDate"], errors="coerce")
attendance["CheckinTime"] = pd.to_datetime(attendance["CheckinTime"], errors="coerce")

# Feature engineering
attendance_agg = attendance.groupby("PhoneNumber").size().reset_index(name="TotalVisits")
data = members.merge(attendance_agg, on="PhoneNumber", how="left").fillna(0)

data["MembershipWeeks"] = ((pd.Timestamp.today() - data["StartDate"]).dt.days / 7).clip(lower=1)
data["AvgVisitsPerWeek"] = data["TotalVisits"] / data["MembershipWeeks"]
data["PaymentRatio"] = data["ReceivedAmount"] / data["NetAmount"]

# Target
today = pd.Timestamp.today()
data["Churn"] = np.where(
    (data["EndDate"] < today) & (data["PlanStatus"].str.lower() != "active"), 1, 0
)

# ML data
features = ["MembershipWeeks", "AvgVisitsPerWeek", "PaymentRatio", "PlanName", "PlanStatus"]
X = pd.get_dummies(data[features], drop_first=True)
y = data["Churn"]

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Save model
with open("models/churn_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ ML model trained and saved as churn_model.pkl")
