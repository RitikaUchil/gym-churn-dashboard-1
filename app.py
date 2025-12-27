# --------------------------
# Gym Owner Dashboard - Streamlit (FINAL with Gradient KPI Circles)
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import re

# --------------------------
# Page Config (must be first)
# --------------------------
st.set_page_config(layout="wide", page_title="Gym Owner Dashboard")

# --------------------------
# Background Image + Glass UI + KPI CSS
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
            background: rgba(255, 255, 255, 0.35);
            backdrop-filter: blur(12px);
            padding: 2rem;
            border-radius: 18px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
        }}

        /* KPI Circle Cards */
        .kpi-circle {{
            width: 170px;
            height: 170px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00c6ff, #0072ff);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: 0 12px 30px rgba(0,0,0,0.4);
            margin: auto;
        }}

        .kpi-circle.orange {{
            background: linear-gradient(135deg, #ff9a00, #ff4e00);
        }}

        .kpi-circle.green {{
            background: linear-gradient(135deg, #00b09b, #96c93d);
        }}

        .kpi-circle.purple {{
            background: linear-gradient(135deg, #a18cd1, #fbc2eb);
        }}

        .kpi-value {{
            font-size: 42px;
            font-weight: 800;
            color: #ffffff;
        }}

        .kpi-label {{
            font-size: 15px;
            color: #ffffff;
            margin-top: 6px;
            text-align: center;
            opacity: 0.95;
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
    # Merge Data
    # --------------------------
    data = members.merge(
        attendance_agg[['PhoneNumber', 'TotalVisits', 'AvgVisitsPerWeek']],
        on='PhoneNumber',
        how='left'
    ).fillna(0)

    # --------------------------
    # PT PLAN LOGIC
    # --------------------------
    def normalize(text):
        return str(text).lower().replace(".", "").replace("-", " ").strip()

    SESSION_KEYWORDS = ["session", "sessions", "sess", "ses"]

    def is_session_based(plan):
        text = normalize(plan)
        for kw in SESSION_KEYWORDS:
            if kw in text:
                return True
        if re.search(r"\b\d+\s*s\b", text):
            return True
        return False

    def extract_sessions(plan):
        match = re.search(r"(\d+)", normalize(plan))
        return int(match.group(1)) if match else np.nan

    def classify_pt(plan):
        if "pt" in normalize(plan):
            return "PT_SESSION_BASED" if is_session_based(plan) else "PT_TIME_BASED"
        return "NON_PT"

    data['PT_Plan_Type'] = data['PlanName'].apply(classify_pt)

    data['EntitledSessions'] = np.where(
        data['PT_Plan_Type'] == "PT_SESSION_BASED",
        data['PlanName'].apply(extract_sessions),
        np.nan
    )

    data['SessionUtilization'] = np.where(
        data['PT_Plan_Type'] == "PT_SESSION_BASED",
        data['TotalVisits'] / data['EntitledSessions'],
        np.nan
    )

    # --------------------------
    # Churn
    # --------------------------
    today = pd.Timestamp.today()
    data['Churn'] = np.where(
        (data['EndDate'] < today) & (data['PlanStatus'].str.lower() != 'active'),
        1, 0
    )

    # --------------------------
    # Smart Risk Logic
    # --------------------------
    def smart_risk(row):
        if row['PT_Plan_Type'] == "PT_SESSION_BASED":
            if row['SessionUtilization'] < 0.5:
                return "High"
            elif row['SessionUtilization'] < 0.8:
                return "Medium"
            return "Low"

        if row['PT_Plan_Type'] == "PT_TIME_BASED":
            if row['AvgVisitsPerWeek'] < 1.5:
                return "High"
            elif row['AvgVisitsPerWeek'] < 3:
                return "Medium"
            return "Low"

        return "High" if row['Churn'] == 1 else "Low"

    data['RiskLevel'] = data.apply(smart_risk, axis=1)

    # --------------------------
    # 🔥 KPI METRICS (GRADIENT CIRCLES)
    # --------------------------
    st.markdown("### 📊 Key Performance Indicators")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="kpi-circle">
            <div class="kpi-value">{len(data)}</div>
            <div class="kpi-label">Total Members</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-circle orange">
            <div class="kpi-value">{len(data[data['RiskLevel'] == "High"])}</div>
            <div class="kpi-label">High Risk Members</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-circle green">
            <div class="kpi-value">{round(data['AvgVisitsPerWeek'].mean(), 2)}</div>
            <div class="kpi-label">Avg Visits / Week</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-circle purple">
            <div class="kpi-value">{round(data['PaymentRatio'].mean(), 2)}</div>
            <div class="kpi-label">Avg Payment Ratio</div>
        </div>
        """, unsafe_allow_html=True)

    # --------------------------
    # Member Table
    # --------------------------
    st.subheader("Member Overview")
    st.dataframe(data[
        ['PhoneNumber', 'PlanName', 'PT_Plan_Type',
         'TotalVisits', 'AvgVisitsPerWeek',
         'EntitledSessions', 'SessionUtilization',
         'PaymentRatio', 'Churn', 'RiskLevel']
    ])

    # --------------------------
    # Visualizations
    # --------------------------
    st.subheader("Risk Distribution")
    fig, ax = plt.subplots()
    sns.countplot(x=data['RiskLevel'], ax=ax)
    st.pyplot(fig)

else:
    st.info("Please upload both Members and Attendance Excel files.")
