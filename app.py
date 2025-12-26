# --------------------------
# Gym Owner Dashboard - Streamlit
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from sklearn.ensemble import RandomForestClassifier

# --------------------------
# Background Image + Glass UI
# --------------------------
def set_background(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}

        .block-container {{
            background: rgba(255, 255, 255, 0.0);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 2rem;
            border-radius: 18px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Call background
set_background("assets/bg.jpg")

# --------------------------
# Page Config
# --------------------------
st.set_page_config(layout="wide", page_title="Gym Owner Dashboard")
st.title("🏋️ Gym Owner Dashboard")

# --------------------------
# 1. File Upload
# --------------------------
members_file = st.file_uploader("Upload Members Excel", type=["xlsx"])
attendance_file = st.file_uploader("Upload Attendance Excel", type=["xlsx"])

if members_file and attendance_file:
    members = pd.read_excel(members_file)
    attendance = pd.read_excel(attendance_file)

    # --------------------------
    # 2. Preprocessing Members
    # --------------------------
    members.rename(columns={
        'Number': 'PhoneNumber',
        'Start Date': 'StartDate',
        'End Date': 'EndDate',
        'Plan Name': 'PlanName',
        'Plan Status': 'PlanStatus',
        'Trainer ID': 'TrainerID',
        'Net Amount': 'NetAmount',
        'Received Amount': 'ReceivedAmount',
        'Amount Pending': 'AmountPending'
    }, inplace=True)

    members['DOB'] = pd.to_datetime(members['DOB'], errors='coerce')
    members['StartDate'] = pd.to_datetime(members['StartDate'], errors='coerce')
    members['EndDate'] = pd.to_datetime(members['EndDate'], errors='coerce')

    members['Age'] = (pd.Timestamp.today() - members['DOB']).dt.days // 365
    members['TrainerAssigned'] = np.where(members['TrainerID'].notna(), 1, 0)
    members['PaymentRatio'] = (members['ReceivedAmount'] / members['NetAmount']).fillna(0)

    # --------------------------
    # 3. Preprocessing Attendance
    # --------------------------
    attendance.rename(columns={
        'Mobile Number': 'PhoneNumber',
        'Checkin Time': 'CheckinTime'
    }, inplace=True)

    attendance['CheckinTime'] = pd.to_datetime(attendance['CheckinTime'], errors='coerce')

    attendance_agg = attendance.groupby('PhoneNumber').agg(
        TotalVisits=('CheckinTime', 'count'),
        LastVisit=('CheckinTime', 'max')
    ).reset_index()

    members_indexed = members.set_index('PhoneNumber')

    def calc_weeks(phone):
        if phone in members_indexed.index:
            start = members_indexed.loc[phone, 'StartDate']
            return max((pd.Timestamp.today() - start).days / 7, 1)
        return 1

    attendance_agg['MembershipWeeks'] = attendance_agg['PhoneNumber'].apply(calc_weeks)
    attendance_agg['AvgVisitsPerWeek'] = attendance_agg['TotalVisits'] / attendance_agg['MembershipWeeks']

    # --------------------------
    # 4. Merge Data
    # --------------------------
    data = members.merge(
        attendance_agg[['PhoneNumber', 'TotalVisits', 'AvgVisitsPerWeek', 'LastVisit']],
        on='PhoneNumber',
        how='left'
    ).fillna(0)

    # --------------------------
    # 5. Churn Target
    # --------------------------
    today = pd.Timestamp.today()
    data['Churn'] = np.where(
        (data['EndDate'] < today) & (data['PlanStatus'].str.lower() != 'active'), 1, 0
    )

    # --------------------------
    # 6. Risk Levels
    # --------------------------
    def risk_level(prob):
        if prob >= 0.7:
            return "High"
        elif prob >= 0.4:
            return "Medium"
        return "Low"

    data['ChurnProbability'] = data['Churn']
    data['RiskLevel'] = data['ChurnProbability'].apply(risk_level)

    # --------------------------
    # 7. Summary Metrics
    # --------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Members", len(data))
    c2.metric("High Risk Members", len(data[data['RiskLevel'] == "High"]))
    c3.metric("Avg Visits / Week", round(data['AvgVisitsPerWeek'].mean(), 2))
    c4.metric("Avg Payment Ratio", round(data['PaymentRatio'].mean(), 2))

    st.markdown("---")

    # --------------------------
    # 8. Member Table
    # --------------------------
    st.subheader("Member Overview")
    st.dataframe(data[
        ['PhoneNumber', 'Age', 'PlanName', 'TotalVisits',
         'AvgVisitsPerWeek', 'PaymentRatio', 'Churn', 'RiskLevel']
    ])

    # --------------------------
    # 9. Visualizations
    # --------------------------
    st.subheader("Churn Distribution")
    fig, ax = plt.subplots()
    sns.histplot(data['ChurnProbability'], bins=20, kde=True, ax=ax)
    st.pyplot(fig)

    st.subheader("Plan-wise Distribution")
    fig2, ax2 = plt.subplots()
    sns.barplot(
        x=data['PlanName'].value_counts().index,
        y=data['PlanName'].value_counts().values,
        ax=ax2
    )
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
    st.pyplot(fig2)

else:
    st.info("Please upload both Members and Attendance Excel files to view the dashboard.")
