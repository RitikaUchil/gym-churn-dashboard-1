# --------------------------
# Gym Owner Dashboard - Streamlit (Retention Intelligence Pro)
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import base64
import matplotlib.pyplot as plt

plt.style.use("dark_background")

# --------------------------
# Page Config
# --------------------------
st.set_page_config(page_title="Gym Owner Dashboard", layout="wide")

# --------------------------
# Background Image + Glass UI + Gradient Cards
# --------------------------
def set_background(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
    }}

    .block-container {{
        background: linear-gradient(to bottom right, rgba(0,0,0,0.55), rgba(0,0,0,0.75));
        backdrop-filter: blur(12px);
        padding: 2rem;
        border-radius: 18px;
    }}

    .metric-card {{
        background: rgba(0,0,0,0.85);
        padding: 18px;
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
    }}

    .metric-card p {{
        color: white;
        font-size: 16px;
    }}
    </style>
    """, unsafe_allow_html=True)

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
    # Members Processing
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

    visits = attendance.groupby('PhoneNumber').size().reset_index(name="TotalVisits")
    data = members.merge(visits, on='PhoneNumber', how='left').fillna(0)

    data['MembershipWeeks'] = ((pd.Timestamp.today() - data['StartDate']).dt.days / 7).clip(lower=1)
    data['AvgVisitsPerWeek'] = data['TotalVisits'] / data['MembershipWeeks']

    # --------------------------
    # Churn + Risk
    # --------------------------
    today = pd.Timestamp.today()
    data['Churn'] = np.where(
        (data['EndDate'] < today) & (data['PlanStatus'].str.lower() != 'active'), 1, 0
    )

    data['RiskLevel'] = np.where(
        data['Churn'] == 1, "High",
        np.where(data['AvgVisitsPerWeek'] < 1.5, "Medium", "Low")
    )

    # --------------------------
    # Remedies + Coupons
    # --------------------------
    data['RecommendedAction'] = data['RiskLevel'].map({
        "High": "Personal call + Free PT",
        "Medium": "WhatsApp reminder + Free class",
        "Low": "Maintain engagement"
    })

    data['CouponOffer'] = data['RiskLevel'].map({
        "High": "20% Renewal Discount",
        "Medium": "10% Discount",
        "Low": "Referral Coupon"
    })

    data['RetentionProbability'] = data['RiskLevel'].map({
        "High": 0.30,
        "Medium": 0.55,
        "Low": 0.85
    })

    # --------------------------
    # Filters
    # --------------------------
    st.sidebar.header("Filters")
    risk_filter = st.sidebar.multiselect(
        "Risk Level",
        data['RiskLevel'].unique(),
        default=data['RiskLevel'].unique()
    )

    filtered_data = data[data['RiskLevel'].isin(risk_filter)]

    # --------------------------
    # Gradient Metrics
    # --------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"""<div class="metric-card"><h1>{len(filtered_data)}</h1><p>Total Members</p></div>""",
                unsafe_allow_html=True)
    c2.markdown(f"""<div class="metric-card"><h1>{len(filtered_data[filtered_data['RiskLevel']=="High"])}</h1><p>High Risk</p></div>""",
                unsafe_allow_html=True)
    c3.markdown(f"""<div class="metric-card"><h1>{round(filtered_data['AvgVisitsPerWeek'].mean(),2)}</h1><p>Avg Visits / Week</p></div>""",
                unsafe_allow_html=True)
    c4.markdown(f"""<div class="metric-card"><h1>{round(filtered_data['PaymentRatio'].mean(),2)}</h1><p>Payment Ratio</p></div>""",
                unsafe_allow_html=True)

    st.markdown("---")

    # ==========================
    # 📊 CLEAN & EASY PYPLOT GRAPHS
    # ==========================

    # Risk Distribution (Donut)
    st.subheader("Risk Distribution")
    fig, ax = plt.subplots()
    counts = filtered_data['RiskLevel'].value_counts()
    ax.pie(counts, labels=counts.index, autopct='%1.0f%%', startangle=90,
           wedgeprops={'width': 0.45})
    ax.axis('equal')
    st.pyplot(fig)

    # Avg Visits (Box Plot)
    st.subheader("Engagement Distribution")
    fig, ax = plt.subplots()
    filtered_data.boxplot(column='AvgVisitsPerWeek', by='RiskLevel', ax=ax)
    ax.set_title("Avg Visits per Week by Risk Level")
    ax.set_ylabel("Visits / Week")
    plt.suptitle("")
    st.pyplot(fig)

    # Payment Ratio (Violin)
    st.subheader("Payment Behavior")
    fig, ax = plt.subplots()
    groups = [filtered_data[filtered_data['RiskLevel']==r]['PaymentRatio'] for r in ['High','Medium','Low']]
    ax.violinplot(groups, showmeans=True)
    ax.set_xticks([1,2,3])
    ax.set_xticklabels(['High','Medium','Low'])
    ax.set_ylabel("Payment Ratio")
    st.pyplot(fig)

    # Before vs After Retention (Line)
    st.subheader("📈 Retention Improvement")
    before = filtered_data.groupby('RiskLevel')['Churn'].mean()
    after = filtered_data.groupby('RiskLevel')['RetentionProbability'].mean()

    fig, ax = plt.subplots()
    ax.plot(before.index, 1-before, marker='o', label="Before")
    ax.plot(after.index, after, marker='o', label="After")
    ax.set_ylabel("Retention Rate")
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    # --------------------------
    # Action Table
    # --------------------------
    st.subheader("📋 Recovery Action Plan")
    st.dataframe(
        filtered_data[['PhoneNumber','RiskLevel',
                       'RecommendedAction','CouponOffer',
                       'RetentionProbability']],
        use_container_width=True
    )

else:
    st.info("Please upload both files")
