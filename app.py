# --------------------------
# Gym Owner Dashboard - Streamlit (Pro Upgrade with Alerts)
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import base64
import plotly.express as px

# --------------------------
# Page Config
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
            background: linear-gradient(to bottom right, rgba(0,0,0,0.5), rgba(0,0,0,0.7));
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
            box-shadow: 0 8px 20px rgba(0,0,0,0.6);
            transition: transform 0.2s;
        }}

        .metric-card:hover {{
            transform: scale(1.05);
        }}

        .metric-card h1 {{
            background: linear-gradient(to right, #00f5ff, #ff00f5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
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
    # Merge Data
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
        (data['EndDate'] < today) & (data['PlanStatus'].str.lower() != 'active'),
        1, 0
    )
    data['RiskLevel'] = np.where(
        data['Churn'] == 1, "High",
        np.where(data['AvgVisitsPerWeek'] < 1.5, "Medium", "Low")
    )

    # --------------------------
    # Sidebar Filters
    # --------------------------
    st.sidebar.header("Filters")
    risk_filter = st.sidebar.multiselect(
        "Select Risk Level",
        options=data['RiskLevel'].unique(),
        default=data['RiskLevel'].unique()
    )
    plan_filter = st.sidebar.multiselect(
        "Select Plan Name",
        options=data['PlanName'].unique(),
        default=data['PlanName'].unique()
    )

    filtered_data = data[(data['RiskLevel'].isin(risk_filter)) & (data['PlanName'].isin(plan_filter))]

    # --------------------------
    # Metrics
    # --------------------------
    # Add two extra metrics: Membership Expiry & Payment Defaulters
    expiring = filtered_data[(filtered_data['EndDate'] - today).dt.days <= 7]
    defaulters = filtered_data[filtered_data['PaymentRatio'] < 0.5]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f'<div class="metric-card"><h1>🏋️ {len(filtered_data)}</h1><p>Total Members</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h1>⚠️ {len(filtered_data[filtered_data["RiskLevel"]=="High"])}</h1><p>High Risk Members</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h1>📊 {round(filtered_data["AvgVisitsPerWeek"].mean(),2)}</h1><p>Avg Visits / Week</p></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><h1>💰 {round(filtered_data["PaymentRatio"].mean(),2)}</h1><p>Avg Payment Ratio</p></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><h1>⏳ {len(expiring)}</h1><p>Expiring Soon</p></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card"><h1>💸 {len(defaulters)}</h1><p>Defaulters</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # --------------------------
    # Table
    # --------------------------
    st.subheader("Member Overview")
    def highlight_risk(row):
        if row['RiskLevel'] == 'High':
            color = 'background-color: #FF4C4C; color:white'
        elif row['RiskLevel'] == 'Medium':
            color = 'background-color: #FFA500; color:black'
        else:
            color = 'background-color: #32CD32; color:black'
        return [color]*len(row)
    
    st.dataframe(
        filtered_data[['PhoneNumber','PlanName','TotalVisits','AvgVisitsPerWeek','PaymentRatio','Churn','RiskLevel']]
        .style.apply(highlight_risk, axis=1)
    )

    # --------------------------
    # Interactive Charts
    # --------------------------
    # Risk Distribution
    st.subheader("Risk Level Distribution")
    risk_counts = filtered_data['RiskLevel'].value_counts().reset_index()
    risk_counts.columns = ['RiskLevel', 'Count']
    fig_risk = px.bar(
        risk_counts, x='RiskLevel', y='Count', color='RiskLevel',
        color_discrete_map={'High':'#FF4C4C','Medium':'#FFA500','Low':'#32CD32'},
        text='Count', title="Risk Distribution", template="plotly_dark"
    )
    fig_risk.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Number of Members", showlegend=False)
    st.plotly_chart(fig_risk, use_container_width=True)

    # Avg Visits Distribution
    st.subheader("Avg Visits per Week")
    fig_visits = px.histogram(filtered_data, x='AvgVisitsPerWeek', nbins=15, color_discrete_sequence=['#00f5ff'], template="plotly_dark")
    st.plotly_chart(fig_visits, use_container_width=True)

    # Payment Ratio Distribution
    st.subheader("Payment Ratio")
    fig_payment = px.histogram(filtered_data, x='PaymentRatio', nbins=10, color_discrete_sequence=['#ff00f5'], template="plotly_dark")
    st.plotly_chart(fig_payment, use_container_width=True)

    # Churn by Plan
    st.subheader("Churn by Plan")
    churn_plan = filtered_data.groupby('PlanName')['Churn'].sum().reset_index()
    fig_churn = px.bar(churn_plan, x='PlanName', y='Churn', color='Churn', text='Churn', color_continuous_scale='Reds', template="plotly_dark")
    st.plotly_chart(fig_churn, use_container_width=True)

else:
    st.info("Please upload both Members and Attendance Excel files")
