# --------------------------
# Gym Owner Dashboard - Improved Version
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import base64
import plotly.express as px
import io

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Gym Owner Dashboard", layout="wide")

# --------------------------
# Background UI
# --------------------------
def set_background(image_path):
    try:
        with open(image_path, "rb") as img:
            encoded = base64.b64encode(img.read()).decode()

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{encoded}");
                background-size: cover;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except:
        pass

set_background("assets/bg.jpg")

st.title("🏋️ Gym Owner Retention Dashboard (Improved ML)")

# --------------------------
# Upload
# --------------------------
members_file = st.file_uploader("Upload Members Excel", type=["xlsx"])
attendance_file = st.file_uploader("Upload Attendance Excel", type=["xlsx"])

if members_file and attendance_file:

    members = pd.read_excel(members_file)
    attendance = pd.read_excel(attendance_file)

    # --------------------------
    # CLEAN MEMBERS
    # --------------------------
    members.rename(columns={
        "Number": "PhoneNumber",
        "Start Date": "StartDate",
        "End Date": "EndDate",
        "Plan Name": "PlanName",
        "Plan Status": "PlanStatus",
        "Net Amount": "NetAmount",
        "Received Amount": "ReceivedAmount",
    }, inplace=True)

    members["StartDate"] = pd.to_datetime(members["StartDate"], errors="coerce")
    members["EndDate"] = pd.to_datetime(members["EndDate"], errors="coerce")

    members["PaymentRatio"] = (members["ReceivedAmount"] / members["NetAmount"]).fillna(0)

    # --------------------------
    # CLEAN ATTENDANCE
    # --------------------------
    attendance.rename(columns={
        "Mobile Number": "PhoneNumber",
        "Checkin Time": "CheckinTime"
    }, inplace=True)

    attendance["CheckinTime"] = pd.to_datetime(attendance["CheckinTime"])

    attendance_agg = attendance.groupby("PhoneNumber").agg(
        TotalVisits=("CheckinTime", "count")
    ).reset_index()

    # --------------------------
    # MERGE
    # --------------------------
    data = members.merge(attendance_agg, on="PhoneNumber", how="left").fillna(0)

    data["MembershipWeeks"] = ((pd.Timestamp.today() - data["StartDate"]).dt.days / 7).clip(lower=1)
    data["AvgVisitsPerWeek"] = data["TotalVisits"] / data["MembershipWeeks"]

    # --------------------------
    # ✅ IMPROVED CHURN LOGIC
    # --------------------------
    def churn_score(row):
        score = 0

        if row["EndDate"] < pd.Timestamp.today():
            score += 1
        if row["AvgVisitsPerWeek"] < 1.5:
            score += 1
        if row["PaymentRatio"] < 0.8:
            score += 1

        return score

    data["ChurnScore"] = data.apply(churn_score, axis=1)
    data["Churn"] = np.where(data["ChurnScore"] >= 2, 1, 0)

    # --------------------------
    # ML MODEL
    # --------------------------
    features = ["MembershipWeeks", "AvgVisitsPerWeek", "PaymentRatio", "PlanName", "PlanStatus"]

    X = pd.get_dummies(data[features], drop_first=True)
    y = data["Churn"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # --------------------------
    # ✅ FIXED PREDICTION
    # --------------------------
    X_full = pd.get_dummies(data[features], drop_first=True)
    X_full = X_full.reindex(columns=X_train.columns, fill_value=0)

    data["ChurnProbability"] = model.predict_proba(X_full)[:, 1]

    # --------------------------
    # RISK LEVEL
    # --------------------------
    def risk(p):
        if p > 0.7:
            return "High"
        elif p > 0.4:
            return "Medium"
        return "Low"

    data["RiskLevel"] = data["ChurnProbability"].apply(risk)
    data["RetentionProbability"] = 1 - data["ChurnProbability"]

    # --------------------------
    # FEATURE IMPORTANCE 🔥
    # --------------------------
    st.subheader("🔥 Feature Importance")
    importance = pd.Series(model.feature_importances_, index=X_train.columns)
    st.bar_chart(importance.sort_values(ascending=False))

    # --------------------------
    # FILTER
    # --------------------------
    st.sidebar.header("Filters")
    risk_filter = st.sidebar.multiselect(
        "Risk Level",
        data["RiskLevel"].unique(),
        default=data["RiskLevel"].unique(),
    )

    filtered_data = data[data["RiskLevel"].isin(risk_filter)]

    # --------------------------
    # METRICS
    # --------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Members", len(filtered_data))
    c2.metric("High Risk", len(filtered_data[filtered_data["RiskLevel"] == "High"]))
    c3.metric("Avg Visits/Week", round(filtered_data["AvgVisitsPerWeek"].mean(), 2))
    c4.metric("Payment Ratio", round(filtered_data["PaymentRatio"].mean(), 2))

    st.markdown("---")

    # --------------------------
    # CHARTS
    # --------------------------
    st.subheader("Risk Distribution")
    fig = px.pie(filtered_data, names="RiskLevel", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Engagement vs Risk")
    fig2 = px.box(filtered_data, x="RiskLevel", y="AvgVisitsPerWeek")
    st.plotly_chart(fig2, use_container_width=True)

    # --------------------------
    # ACTION TABLE
    # --------------------------
    def action(row):
        if row["RiskLevel"] == "High":
            return "Call + Offer Discount"
        elif row["RiskLevel"] == "Medium":
            return "Reminder + Free Session"
        return "Maintain"

    data["Action"] = data.apply(action, axis=1)

    st.subheader("📋 Action Plan")
    st.dataframe(data[["Name", "PhoneNumber", "RiskLevel", "Action", "RetentionProbability"]])

    # --------------------------
    # DOWNLOAD
    # --------------------------
    buffer = io.BytesIO()
    data.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button("Download Excel", buffer, "output.xlsx")

else:
    st.info("Upload both files")
