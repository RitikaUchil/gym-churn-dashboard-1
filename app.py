# --------------------------
# Gym Owner Dashboard - Streamlit (Dynamic Upload + Labels Fix)
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

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
    members.rename(columns={'Number':'PhoneNumber','DOB':'DOB','Start Date':'StartDate',
                            'End Date':'EndDate','Plan Name':'PlanName','Plan Status':'PlanStatus',
                            'Trainer ID':'TrainerID','Net Amount':'NetAmount',
                            'Received Amount':'ReceivedAmount','Amount Pending':'AmountPending'}, inplace=True)
    
    members['DOB'] = pd.to_datetime(members['DOB'], errors='coerce')
    members['StartDate'] = pd.to_datetime(members['StartDate'], errors='coerce')
    members['EndDate'] = pd.to_datetime(members['EndDate'], errors='coerce')
    members['Age'] = (pd.Timestamp.today() - members['DOB']).dt.days // 365
    members['TrainerAssigned'] = np.where(members['TrainerID'].notna(),1,0)
    members['PaymentRatio'] = members['ReceivedAmount'] / members['NetAmount']
    members['PaymentRatio'] = members['PaymentRatio'].fillna(0)
    
    # --------------------------
    # 3. Preprocessing Attendance
    # --------------------------
    attendance.rename(columns={'Mobile Number':'PhoneNumber','Checkin Time':'CheckinTime'}, inplace=True)
    attendance['CheckinTime'] = pd.to_datetime(attendance['CheckinTime'], errors='coerce')
    
    attendance_agg = attendance.groupby('PhoneNumber').agg(
        TotalVisits=('CheckinTime','count'),
        LastVisit=('CheckinTime','max')
    ).reset_index()
    
    # MembershipWeeks calculation
    members_indexed = members.set_index('PhoneNumber')
    def calc_weeks(phone):
        if phone in members_indexed.index:
            start = members_indexed.loc[phone, 'StartDate']
            return ((pd.Timestamp.today() - start).days / 7)
        else:
            return 0
    attendance_agg['MembershipWeeks'] = attendance_agg['PhoneNumber'].apply(calc_weeks)
    attendance_agg['AvgVisitsPerWeek'] = attendance_agg['TotalVisits'] / attendance_agg['MembershipWeeks']
    attendance_agg['AvgVisitsPerWeek'] = attendance_agg['AvgVisitsPerWeek'].fillna(0)
    
    # --------------------------
    # 4. Merge Members + Attendance
    # --------------------------
    data = members.merge(attendance_agg[['PhoneNumber','TotalVisits','AvgVisitsPerWeek','LastVisit']], 
                         on='PhoneNumber', how='left')
    data['TotalVisits'] = data['TotalVisits'].fillna(0)
    data['AvgVisitsPerWeek'] = data['AvgVisitsPerWeek'].fillna(0)
    
    # --------------------------
    # 5. Churn Target
    # --------------------------
    today = pd.Timestamp.today()
    data['Churn'] = np.where((data['EndDate'] < today) & (data['PlanStatus'].str.lower() != 'active'),1,0)
    
    # --------------------------
    # 6. Risk Levels
    # --------------------------
    def risk_level(prob):
        if prob >= 0.7:
            return "High"
        elif prob >= 0.4:
            return "Medium"
        else:
            return "Low"
    
    data['ChurnProbability'] = data['Churn']
    data['RiskLevel'] = data['ChurnProbability'].apply(risk_level)
    
    # --------------------------
    # 7. Summary Metrics
    # --------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Members", len(data))
    c2.metric("High Risk Members", len(data[data['RiskLevel']=="High"]))
    c3.metric("Avg Visits/Week", round(data['AvgVisitsPerWeek'].mean(),2))
    c4.metric("Avg Payment Ratio", round(data['PaymentRatio'].mean(),2))
    
    st.markdown("---")
    
    # --------------------------
    # 8. Member Overview Table
    # --------------------------
    st.subheader("Member Overview")
    st.dataframe(data[['PhoneNumber','Age','PlanName','TotalVisits','AvgVisitsPerWeek',
                       'PaymentRatio','Churn','ChurnProbability','RiskLevel']])
    
    # --------------------------
    # 9. Visualizations with Rotated Labels
    # --------------------------
    
    st.subheader("Churn Probability Distribution")
    fig, ax = plt.subplots(figsize=(8,4))
    sns.histplot(data['ChurnProbability'], bins=20, kde=True, color='orange', ax=ax)
    ax.set_xlabel("Churn Probability")
    ax.set_ylabel("Number of Members")
    plt.tight_layout()  # Prevent overlapping
    st.pyplot(fig)
    
    st.subheader("Plan-wise Member Distribution")
    plan_counts = data['PlanName'].value_counts()
    fig2, ax2 = plt.subplots(figsize=(10,5))
    sns.barplot(x=plan_counts.index, y=plan_counts.values, palette="viridis", ax=ax2)
    ax2.set_ylabel("Number of Members")
    ax2.set_xlabel("Plan Name")
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')  # Rotate x-axis labels
    plt.tight_layout()
    st.pyplot(fig2)
    
    st.subheader("Risk Level Distribution")
    risk_counts = data['RiskLevel'].value_counts()
    fig3, ax3 = plt.subplots(figsize=(6,4))
    colors = ["red","yellow","green"]
    sns.barplot(x=risk_counts.index, y=risk_counts.values, palette=colors, ax=ax3)
    ax3.set_ylabel("Number of Members")
    ax3.set_xlabel("Risk Level")
    ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)  # No rotation needed here
    plt.tight_layout()
    st.pyplot(fig3)
    
else:
    st.info("Please upload both Members and Attendance Excel files to view the dashboard.")
