# --------------------------
# Gym Owner Dashboard - Streamlit
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import base64

# --------------------------
# Page Config (MUST BE FIRST)
# --------------------------
st.set_page_config(
    page_title="Gym Owner Dashboard",
    layout="wide"
)

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
            background: rgba(0,0,0,0.55);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 2rem;
            border-radius: 18px;
        }}

        .metric-card {{
            background: rgba(0,0,0,0.85);
            padding: 16px;
            border-radius: 14px;
            text-align: center;
        }}

        .metric-card h1 {{
            color: #00f5ff;
            font-size: 36px;
            margin-bottom: 0;
        }}

        .metric-card p {{
            color: #ffffff;
            font-size: 16px;
            margin-top: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("assets/bg.jpg")

# --------------------------
# Title
# --------------------------
st.title("🏋️ Gym Owner Dashboard")

# --------------------------
# File Upload
# --------------------------
members_file = st.file_uploader("Upload Members Excel", type=["xlsx"])
attendance_file = st.file_uploader("Upload Attendance Excel", type=["xlsx"])

if members_file and attendance_file:

    members = pd.read_excel(members_file)
    attendance = pd.read_excel(attendance_file)

    # --------------------------
    # Members Preprocessing
    # --------------------------
    members.rename(columns={
        'Number': 'PhoneNumber',
        'Start Date': 'StartDate',
        'End Date': 'EndDate',
        'Plan Name': 'PlanName',
        'Plan Status': 'PlanStatus',
        'Trainer ID': 'TrainerID',
        'Net Amount': 'NetAmount',
        'Received Amount': 'ReceivedAmount'
    }, inplace=True)

    members['DOB'] = pd.to_datetime(members['DOB'], errors='coerce')
    members['StartDate'] = pd.to_datetime(members['StartDate'], errors='coerce')
    members['EndDate'] = pd.to_datetime(members['EndDate'], errors='coerce')

    members['Age'] = (pd.Timestamp.today() - members['DOB']).dt.days // 365
    members['PaymentRatio'] = (members['ReceivedAmount'] / members['NetAmount']).fillna(0)

    # --------------------------
    # Attendance Preprocessing
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

    members_idx = members.set_index('PhoneNumber')

    def calc_weeks(phone):
        if phone in members_idx.index:
            start = members_idx.loc[phone, 'StartDate']
            return max((pd.Timestamp.today() - start).days / 7, 1)
        return 1

    attendance_agg['MembershipWeeks'] = attendance_agg['PhoneNumber'].apply(calc_weeks)
    attendance_agg['AvgVisitsPerWeek'] = attendance_agg['TotalVisits'] / attendance_agg['MembershipWeeks']

    # --------------------------
    # Merge
    # --------------------------
    data = members.merge(
        attendance_agg[['PhoneNumber', 'TotalVisits', 'AvgVisitsPerWeek']],
        on='PhoneNumber',
        how='left'
    ).fillna(0)

    # --------------------------
    # Churn + Risk
    # --------------------------
    today = pd.Timestamp.today()

    data['Churn'] = np.where(
        (data['EndDate'] < today) &
        (data['PlanStatus'].str.lower() != 'active'),
        1, 0
    )

    data['RiskLevel'] = np.where(
        data['Churn'] == 1, "High",
        np.where(data['AvgVisitsPerWeek'] < 1.5, "Medium", "Low")
    )

    # --------------------------
    # Metrics (VISIBLE & CLEAN)
    # --------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(
        f'<div class="metric-card"><h1>{len(data)}</h1><p>Total Members</p></div>',
        unsafe_allow_html=True
    )

    c2.markdown(
        f'<div class="metric-card"><h1>{len(data[data["RiskLevel"]=="High"])}</h1><p>High Risk Members</p></div>',
        unsafe_allow_html=True
    )

    c3.markdown(
        f'<div class="metric-card"><h1>{round(data["AvgVisitsPerWeek"].mean(),2)}</h1><p>Avg Visits / Week</p></div>',
        unsafe_allow_html=True
    )

    c4.markdown(
        f'<div class="metric-card"><h1>{round(data["PaymentRatio"].mean(),2)}</h1><p>Avg Payment Ratio</p></div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    # --------------------------
    # Table
    # --------------------------
    st.subheader("Member Overview")
    st.dataframe(
        data[['PhoneNumber', 'PlanName', 'TotalVisits',
              'AvgVisitsPerWeek', 'PaymentRatio', 'Churn', 'RiskLevel']]
    )

    # --------------------------
    # Dark Charts (NO white bg)
    # --------------------------
    sns.set_style("dark")

    st.subheader("Risk Distribution")
    fig, ax = plt.subplots(facecolor='none')
    sns.countplot(x=data['RiskLevel'], ax=ax)
    ax.set_facecolor("none")
    st.pyplot(fig)

else:
    st.info("Please upload both Members and Attendance Excel files")
