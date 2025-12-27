# ==========================================================
# Gym Owner Dashboard - FINAL PRO VERSION
# ==========================================================

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import base64
import re

# --------------------------
# PAGE CONFIG (FIRST!)
# --------------------------
st.set_page_config(
    page_title="Gym Owner Dashboard",
    layout="wide"
)

# --------------------------
# BACKGROUND + ADVANCED CSS
# --------------------------
def set_background(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(f"""
    <style>

    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
    }}

    /* ===== KPI PANEL ===== */
    .kpi-panel {{
        background: rgba(5, 5, 10, 0.88);
        padding: 35px;
        border-radius: 24px;
        box-shadow: 0 30px 70px rgba(0,0,0,0.8);
        margin-bottom: 35px;
    }}

    .kpi-card {{
        height: 170px;
        border-radius: 22px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        transition: transform 0.4s ease, box-shadow 0.4s ease;
    }}

    .kpi-card:hover {{
        transform: translateY(-12px) scale(1.06);
        box-shadow: 0 35px 70px rgba(0,0,0,0.9);
    }}

    .blue {{ background: linear-gradient(135deg,#0f2027,#2c5364); }}
    .green {{ background: linear-gradient(135deg,#11998e,#38ef7d); }}
    .purple {{ background: linear-gradient(135deg,#6a11cb,#2575fc); }}

    /* Pulsing HIGH RISK */
    .red {{
        background: linear-gradient(135deg,#cb2d3e,#ef473a);
        animation: pulse 1.5s infinite;
    }}

    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(239,71,58,0.7); }}
        70% {{ box-shadow: 0 0 0 25px rgba(239,71,58,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(239,71,58,0); }}
    }}

    .kpi-value {{
        font-size: 44px;
        font-weight: 800;
    }}

    .kpi-label {{
        font-size: 15px;
        opacity: 0.9;
        margin-top: 6px;
        text-align: center;
    }}

    /* ===== TABLE STYLING ===== */
    .dataframe {{
        background: rgba(0,0,0,0.75);
        color: white;
    }}

    </style>
    """, unsafe_allow_html=True)

# ⚠️ Make sure this exists
set_background("assets/bg.jpg")

# --------------------------
# TITLE
# --------------------------
st.title("🏋️ Gym Owner Dashboard")

# --------------------------
# FILE UPLOAD
# --------------------------
members_file = st.file_uploader("Upload Members Excel", type=["xlsx"])
attendance_file = st.file_uploader("Upload Attendance Excel", type=["xlsx"])

if members_file and attendance_file:

    # --------------------------
    # LOAD DATA
    # --------------------------
    members = pd.read_excel(members_file)
    attendance = pd.read_excel(attendance_file)

    # --------------------------
    # MEMBERS PREPROCESSING
    # --------------------------
    members.rename(columns={
        'Number':'PhoneNumber',
        'Start Date':'StartDate',
        'End Date':'EndDate',
        'Plan Name':'PlanName',
        'Plan Status':'PlanStatus',
        'Net Amount':'NetAmount',
        'Received Amount':'ReceivedAmount'
    }, inplace=True)

    members['StartDate'] = pd.to_datetime(members['StartDate'], errors='coerce')
    members['EndDate'] = pd.to_datetime(members['EndDate'], errors='coerce')
    members['PaymentRatio'] = (members['ReceivedAmount'] / members['NetAmount']).fillna(0)

    # --------------------------
    # ATTENDANCE
    # --------------------------
    attendance.rename(columns={
        'Mobile Number':'PhoneNumber',
        'Checkin Time':'CheckinTime'
    }, inplace=True)

    attendance['CheckinTime'] = pd.to_datetime(attendance['CheckinTime'], errors='coerce')

    visits = attendance.groupby('PhoneNumber').size().reset_index(name='TotalVisits')

    data = members.merge(visits, on='PhoneNumber', how='left').fillna(0)

    # --------------------------
    # PT PLAN LOGIC
    # --------------------------
    def normalize(text):
        return str(text).lower().replace(".", "").replace("-", " ")

    def is_session_based(plan):
        return any(k in normalize(plan) for k in ["session", "sessions", "sess", "ses"])

    def extract_sessions(plan):
        m = re.search(r"(\d+)", normalize(plan))
        return int(m.group(1)) if m else np.nan

    def classify_pt(plan):
        if "pt" in normalize(plan):
            return "PT_SESSION_BASED" if is_session_based(plan) else "PT_TIME_BASED"
        return "NON_PT"

    data['PT_Plan_Type'] = data['PlanName'].apply(classify_pt)
    data['EntitledSessions'] = np.where(
        data['PT_Plan_Type']=="PT_SESSION_BASED",
        data['PlanName'].apply(extract_sessions),
        np.nan
    )

    data['SessionUtilization'] = np.where(
        data['PT_Plan_Type']=="PT_SESSION_BASED",
        data['TotalVisits']/data['EntitledSessions'],
        np.nan
    )

    # --------------------------
    # CHURN + RISK
    # --------------------------
    today = pd.Timestamp.today()

    data['Churn'] = np.where(
        (data['EndDate'] < today) & (data['PlanStatus'].str.lower() != 'active'),
        1, 0
    )

    def risk_logic(row):
        if row['PT_Plan_Type']=="PT_SESSION_BASED":
            if row['SessionUtilization'] < 0.5: return "High"
            elif row['SessionUtilization'] < 0.8: return "Medium"
            return "Low"

        if row['PT_Plan_Type']=="PT_TIME_BASED":
            if row['TotalVisits'] < 4: return "High"
            elif row['TotalVisits'] < 8: return "Medium"
            return "Low"

        return "High" if row['Churn']==1 else "Low"

    data['RiskLevel'] = data.apply(risk_logic, axis=1)

    # --------------------------
    # KPI PANEL
    # --------------------------
    st.markdown("<div class='kpi-panel'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"""
    <div class="kpi-card blue">
        <div class="kpi-value">{len(data)}</div>
        <div class="kpi-label">Total Members</div>
    </div>
    """, unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="kpi-card red">
        <div class="kpi-value">{len(data[data['RiskLevel']=="High"])}</div>
        <div class="kpi-label">High Risk Members</div>
    </div>
    """, unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="kpi-card green">
        <div class="kpi-value">{round(data['TotalVisits'].mean(),2)}</div>
        <div class="kpi-label">Avg Visits</div>
    </div>
    """, unsafe_allow_html=True)

    c4.markdown(f"""
    <div class="kpi-card purple">
        <div class="kpi-value">{round(data['PaymentRatio'].mean(),2)}</div>
        <div class="kpi-label">Payment Ratio</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------
    # INTERACTIVE 3D-FEEL GRAPH
    # --------------------------
    st.subheader("📊 Risk Distribution")

    fig = px.bar(
        data,
        x="RiskLevel",
        color="RiskLevel",
        template="plotly_dark",
        text_auto=True
    )

    fig.update_traces(marker_line_width=2)
    fig.update_layout(height=420, showlegend=False)

    st.plotly_chart(fig, use_container_width=True)

    # --------------------------
    # MEMBER TABLE (RISK COLORED)
    # --------------------------
    st.subheader("👥 Member Overview")

    def color_risk(val):
        if val=="High": return "background-color:#8b0000;color:white;"
        if val=="Medium": return "background-color:#ff8c00;color:black;"
        return "background-color:#006400;color:white;"

    st.dataframe(
        data[['PhoneNumber','PlanName','PT_Plan_Type',
              'TotalVisits','EntitledSessions',
              'SessionUtilization','PaymentRatio',
              'Churn','RiskLevel']]
        .style.applymap(color_risk, subset=['RiskLevel']),
        use_container_width=True
    )

else:
    st.info("📂 Please upload both Members and Attendance Excel files.")
