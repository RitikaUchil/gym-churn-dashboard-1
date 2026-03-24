# --------------------------
# Gym Owner Dashboard - FINAL FIXED VERSION
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import io

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Gym Dashboard", layout="wide")

st.title("🏋️ Gym Retention Dashboard (Final Fixed ML)")

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

    # 🔥 IMPORTANT FEATURES
    today = pd.Timestamp.today()

    attendance_agg = attendance.groupby("PhoneNumber").agg(
        TotalVisits=("CheckinTime", "count"),
        LastVisit=("CheckinTime", "max")
    ).reset_index()

    attendance_agg["DaysSinceLastVisit"] = (today - attendance_agg["LastVisit"]).dt.days

    # --------------------------
    # MERGE
    # --------------------------
    data = members.merge(attendance_agg, on="PhoneNumber", how="left")

    data["TotalVisits"] = data["TotalVisits"].fillna(0)
    data["DaysSinceLastVisit"] = data["DaysSinceLastVisit"].fillna(999)

    data["MembershipWeeks"] = ((today - data["StartDate"]).dt.days / 7).clip(lower=1)
    data["AvgVisitsPerWeek"] = data["TotalVisits"] / data["MembershipWeeks"]

    # --------------------------
    # ✅ SMART CHURN LOGIC (BALANCED)
    # --------------------------
    def churn_label(row):
        if row["EndDate"] < today:
            return 1
        if row["DaysSinceLastVisit"] > 20:
            return 1
        if row["AvgVisitsPerWeek"] < 1:
            return 1
        return 0

    data["Churn"] = data.apply(churn_label, axis=1)

    # --------------------------
    # ML MODEL
    # --------------------------
    features = [
        "MembershipWeeks",
        "AvgVisitsPerWeek",
        "PaymentRatio",
        "DaysSinceLastVisit",
        "PlanName",
        "PlanStatus"
    ]

    X = pd.get_dummies(data[features], drop_first=True)
    y = data["Churn"]

    # ⚠️ Important: balance check
    if y.nunique() < 2:
        st.error("⚠️ All data belongs to one class → cannot train ML model")
        st.stop()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=150, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    # FIXED prediction alignment
    X_full = pd.get_dummies(data[features], drop_first=True)
    X_full = X_full.reindex(columns=X_train.columns, fill_value=0)

    data["ChurnProbability"] = model.predict_proba(X_full)[:, 1]

    # --------------------------
    # ✅ BETTER RISK SEGMENTATION
    # --------------------------
    def risk(p):
        if p > 0.65:
            return "High"
        elif p > 0.35:
            return "Medium"
        return "Low"

    data["RiskLevel"] = data["ChurnProbability"].apply(risk)
    data["RetentionProbability"] = 1 - data["ChurnProbability"]

    # --------------------------
    # METRICS
    # --------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Members", len(data))
    c2.metric("High Risk", len(data[data["RiskLevel"] == "High"]))
    c3.metric("Medium Risk", len(data[data["RiskLevel"] == "Medium"]))
    c4.metric("Low Risk", len(data[data["RiskLevel"] == "Low"]))

    st.markdown("---")

    # --------------------------
    # CHARTS
    # --------------------------
    st.subheader("Risk Distribution")
    fig = px.pie(data, names="RiskLevel", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Days Since Last Visit vs Risk 🔥")
    fig2 = px.box(data, x="RiskLevel", y="DaysSinceLastVisit")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Visits per Week vs Risk")
    fig3 = px.box(data, x="RiskLevel", y="AvgVisitsPerWeek")
    st.plotly_chart(fig3, use_container_width=True)

    # --------------------------
    # ACTION PLAN
    # --------------------------
    def action(row):
        if row["RiskLevel"] == "High":
            return "🚨 Call + Heavy Discount"
        elif row["RiskLevel"] == "Medium":
            return "⚠️ Reminder + Free Session"
        return "✅ Maintain Engagement"

    data["Action"] = data.apply(action, axis=1)

    st.subheader("📋 Action Plan")
    st.dataframe(data[[
        "Name",
        "PhoneNumber",
        "RiskLevel",
        "DaysSinceLastVisit",
        "AvgVisitsPerWeek",
        "Action",
        "RetentionProbability"
    ]])

    # --------------------------
    # DOWNLOAD
    # --------------------------
    buffer = io.BytesIO()
    data.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button("📥 Download Excel", buffer, "gym_output.xlsx")

else:
    st.info("Upload both files")
