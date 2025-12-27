# --------------------------
# Gym Owner Dashboard - Streamlit (Retention Intelligence Pro)
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import base64
import plotly.express as px

# --------------------------
# Page Config
# --------------------------
st.set_page_config(page_title="Gym Owner Dashboard", layout="wide")

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
        }}
        .block-container {{
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 16px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("assets/bg.jpg")

# --------------------------
# Title
# --------------------------
st.title("🏋️ Gym Owner Retention Dashboard")

# --------------------------
# Upload Files
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
        'Net Amount': 'NetAmount',
        'Received Amount': 'ReceivedAmount'
    }, inplace=True)

    members['DOB'] = pd.to_datetime(members['DOB'], errors='coerce')
    members['StartDate'] = pd.to_datetime(members['StartDate'], errors='coerce')
    members['EndDate'] = pd.to_datetime(members['EndDate'], errors='coerce')

    members['PaymentRatio'] = (members['ReceivedAmount'] / members['NetAmount']).fillna(0)

    # --------------------------
    # Attendance Processing
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

    data = members.merge(attendance_agg, on='PhoneNumber', how='left').fillna(0)

    data['MembershipWeeks'] = ((pd.Timestamp.today() - data['StartDate']).dt.days / 7).clip(lower=1)
    data['AvgVisitsPerWeek'] = data['TotalVisits'] / data['MembershipWeeks']

    # --------------------------
    # Churn + Risk Level
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
    # Remedy Recommendation
    # --------------------------
    def recommend_action(row):
        if row['RiskLevel'] == 'High':
            if row['AvgVisitsPerWeek'] < 0.5:
                return "Personal call + Free PT"
            elif row['PaymentRatio'] < 0.7:
                return "Payment follow-up + Flexible plan"
            else:
                return "Renewal discount offer"
        elif row['RiskLevel'] == 'Medium':
            return "WhatsApp reminder + Free class"
        else:
            return "Maintain engagement"

    data['RecommendedAction'] = data.apply(recommend_action, axis=1)

    # --------------------------
    # Coupon Assignment
    # --------------------------
    def assign_coupon(row):
        if row['RiskLevel'] == 'High':
            return "20% Renewal Discount"
        elif row['RiskLevel'] == 'Medium':
            return "10% Discount / Free Class"
        else:
            return "Referral Coupon"

    data['CouponOffer'] = data.apply(assign_coupon, axis=1)

    # --------------------------
    # Coupon Expiry
    # --------------------------
    def coupon_expiry(row):
        if row['RiskLevel'] == 'High':
            return today + pd.Timedelta(days=7)
        elif row['RiskLevel'] == 'Medium':
            return today + pd.Timedelta(days=14)
        else:
            return today + pd.Timedelta(days=30)

    data['CouponExpiry'] = data.apply(coupon_expiry, axis=1)

    # --------------------------
    # Retention Probability (AFTER Action)
    # --------------------------
    def retention_prob(row):
        if row['RiskLevel'] == 'High':
            return 0.30
        elif row['RiskLevel'] == 'Medium':
            return 0.55
        else:
            return 0.85

    data['RetentionProbability'] = data.apply(retention_prob, axis=1)

    # --------------------------
    # BEFORE vs AFTER Retention
    # --------------------------
    before_retention = data.groupby('RiskLevel')['Churn'].mean().reset_index()
    before_retention['RetentionRate'] = 1 - before_retention['Churn']
    before_retention['Stage'] = 'Before Action'

    after_retention = data.groupby('RiskLevel')['RetentionProbability'].mean().reset_index()
    after_retention.rename(columns={'RetentionProbability': 'RetentionRate'}, inplace=True)
    after_retention['Stage'] = 'After Action'

    retention_compare = pd.concat([
        before_retention[['RiskLevel','RetentionRate','Stage']],
        after_retention[['RiskLevel','RetentionRate','Stage']]
    ])

    # --------------------------
    # Sidebar Filters
    # --------------------------
    st.sidebar.header("Filters")
    risk_filter = st.sidebar.multiselect(
        "Risk Level",
        options=data['RiskLevel'].unique(),
        default=data['RiskLevel'].unique()
    )

    filtered_data = data[data['RiskLevel'].isin(risk_filter)]

    # --------------------------
    # Metrics
    # --------------------------
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Members", len(filtered_data))
    c2.metric("High Risk Members", len(filtered_data[filtered_data['RiskLevel']=="High"]))
    c3.metric("Avg Retention Probability",
              f"{round(filtered_data['RetentionProbability'].mean()*100,1)}%")

    st.markdown("---")

    # --------------------------
    # BEFORE vs AFTER Chart
    # --------------------------
    st.subheader("📊 Before vs After Retention Impact")

    fig_retention = px.bar(
        retention_compare,
        x='RiskLevel',
        y='RetentionRate',
        color='Stage',
        barmode='group',
        text_auto='.0%',
        template="plotly_dark",
        title="Retention Improvement After Remedies & Coupons"
    )

    fig_retention.update_layout(
        yaxis_tickformat=".0%",
        yaxis_title="Retention Rate",
        xaxis_title=""
    )

    st.plotly_chart(fig_retention, use_container_width=True)

    # --------------------------
    # Smart Action Table
    # --------------------------
    st.subheader("📋 Member Recovery Action Plan")

    st.dataframe(
        filtered_data[['PhoneNumber','RiskLevel',
                       'RecommendedAction','CouponOffer',
                       'CouponExpiry','RetentionProbability']],
        use_container_width=True
    )

else:
    st.info("Please upload Members & Attendance Excel files")
