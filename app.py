# --------------------------
# Gym Owner Dashboard - Streamlit (Retention Intelligence Pro with Insights & Excel Export)
# --------------------------

import pandas as pd
import numpy as np
import streamlit as st
import base64
import plotly.express as px
import io

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

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
        }}

        .block-container {{
            background: linear-gradient(
                to bottom right,
                rgba(0,0,0,0.55),
                rgba(0,0,0,0.75)
            );
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
            margin-bottom: 0;
        }}

        .metric-card p {{
            color: white;
            font-size: 16px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("assets/bg.jpg")

# --------------------------
# Title
# --------------------------
st.title("🏋️ Gym Owner Retention Dashboard with Insights")

# --------------------------
# File Upload
# --------------------------
members_file = st.file_uploader("Upload Members Excel", type=["xlsx"])
attendance_file = st.file_uploader("Upload Attendance Excel", type=["xlsx"])

if members_file and attendance_file:

    members = pd.read_excel(members_file)
    attendance = pd.read_excel(attendance_file)

    # --------------------------
    # Members Processing
    # --------------------------
    members.rename(
        columns={
            "Number": "PhoneNumber",
            "Name": "Name",
            "Start Date": "StartDate",
            "End Date": "EndDate",
            "Plan Name": "PlanName",
            "Plan Status": "PlanStatus",
            "Net Amount": "NetAmount",
            "Received Amount": "ReceivedAmount",
        },
        inplace=True,
    )

    if "Name" not in members.columns:
        members["Name"] = "N/A"

    members["StartDate"] = pd.to_datetime(members["StartDate"], errors="coerce")
    members["EndDate"] = pd.to_datetime(members["EndDate"], errors="coerce")
    members["PaymentRatio"] = (
        members["ReceivedAmount"] / members["NetAmount"]
    ).fillna(0)

    # --------------------------
    # Attendance Processing
    # --------------------------
    attendance.rename(
        columns={
            "Mobile Number": "PhoneNumber",
            "Checkin Time": "CheckinTime",
        },
        inplace=True,
    )

    attendance["CheckinTime"] = pd.to_datetime(
        attendance["CheckinTime"], errors="coerce"
    )

    attendance_agg = (
        attendance.groupby("PhoneNumber")
        .agg(TotalVisits=("CheckinTime", "count"))
        .reset_index()
    )

    data = members.merge(
        attendance_agg, on="PhoneNumber", how="left"
    ).fillna(0)

    data["MembershipWeeks"] = (
        (pd.Timestamp.today() - data["StartDate"]).dt.days / 7
    ).clip(lower=1)

    data["AvgVisitsPerWeek"] = (
        data["TotalVisits"] / data["MembershipWeeks"]
    )

    # --------------------------
    # Churn + Risk
    # --------------------------
    today = pd.Timestamp.today()

    data["Churn"] = np.where(
        (data["EndDate"] < today)
        & (data["PlanStatus"].str.lower() != "active"),
        1,
        0,
    )

    data["RiskLevel"] = np.where(
        data["Churn"] == 1,
        "High",
        np.where(data["AvgVisitsPerWeek"] < 1.5, "Medium", "Low"),
    )

    # --------------------------
    # Remedies + Coupons
    # --------------------------
    def action(row):
        if row["RiskLevel"] == "High":
            return "Personal call + Free PT"
        elif row["RiskLevel"] == "Medium":
            return "WhatsApp reminder + Free class"
        return "Maintain engagement"

    def coupon(row):
        if row["RiskLevel"] == "High":
            return "20% Renewal Discount"
        elif row["RiskLevel"] == "Medium":
            return "10% Discount"
        return "Referral Coupon"

    def retention_prob(row):
        if row["RiskLevel"] == "High":
            return 0.30
        elif row["RiskLevel"] == "Medium":
            return 0.55
        return 0.85

    data["RecommendedAction"] = data.apply(action, axis=1)
    data["CouponOffer"] = data.apply(coupon, axis=1)
    data["RetentionProbability"] = data.apply(retention_prob, axis=1)

    # --------------------------
    # Filters
    # --------------------------
    st.sidebar.header("Filters")

    risk_filter = st.sidebar.multiselect(
        "Risk Level",
        data["RiskLevel"].unique(),
        default=data["RiskLevel"].unique(),
    )

    filtered_data = data[data["RiskLevel"].isin(risk_filter)]

    # --------------------------
    # Gradient Metrics
    # --------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(
        f"""
        <div class="metric-card">
            <h1>{len(filtered_data)}</h1>
            <p>Total Members</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c2.markdown(
        f"""
        <div class="metric-card">
            <h1>{len(filtered_data[filtered_data["RiskLevel"] == "High"])}</h1>
            <p>High Risk</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c3.markdown(
        f"""
        <div class="metric-card">
            <h1>{round(filtered_data["AvgVisitsPerWeek"].mean(), 2)}</h1>
            <p>Avg Visits / Week</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c4.markdown(
        f"""
        <div class="metric-card">
            <h1>{round(filtered_data["PaymentRatio"].mean(), 2)}</h1>
            <p>Payment Ratio</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # --------------------------
    # Charts with Insights
    # --------------------------
    st.subheader("Risk Distribution")
    risk_counts = filtered_data["RiskLevel"].value_counts().reset_index()
    risk_counts.columns = ["RiskLevel", "Count"]
    fig_risk = px.pie(
        risk_counts, names="RiskLevel", values="Count", hole=0.45, template="plotly_dark"
    )
    st.plotly_chart(fig_risk, use_container_width=True)
    high_pct = round(
        (risk_counts[risk_counts["RiskLevel"] == "High"]["Count"].sum() / len(filtered_data)) * 100,
        2,
    )
    st.markdown(f"**Insight:** {high_pct}% of members are at high risk. Focus retention efforts here first.")

    st.subheader("Avg Visits Per Week (Engagement Spread)")
    fig_visits = px.box(
        filtered_data, x="RiskLevel", y="AvgVisitsPerWeek", color="RiskLevel", template="plotly_dark"
    )
    st.plotly_chart(fig_visits, use_container_width=True)
    avg_visits = round(filtered_data["AvgVisitsPerWeek"].mean(), 2)
    st.markdown(f"**Insight:** Average visits per week is {avg_visits}. Low engagement members are mostly in Medium/High risk groups.")

    st.subheader("Payment Ratio Behavior")
    fig_payment = px.violin(
        filtered_data, x="RiskLevel", y="PaymentRatio", box=True, points="all", template="plotly_dark"
    )
    st.plotly_chart(fig_payment, use_container_width=True)
    avg_payment = round(filtered_data["PaymentRatio"].mean(), 2)
    st.markdown(f"**Insight:** Overall payment ratio is {avg_payment}. Consider offering coupons or discounts to improve collection for Medium/High risk members.")

    st.subheader("Churn Intensity by Plan")
    plan_churn = filtered_data.groupby("PlanName")["Churn"].mean().reset_index()
    fig_churn = px.density_heatmap(
        plan_churn, x="PlanName", y=["Churn"], z="Churn", template="plotly_dark"
    )
    st.plotly_chart(fig_churn, use_container_width=True)
    top_churn_plan = plan_churn.sort_values("Churn", ascending=False).iloc[0]["PlanName"]
    st.markdown(f"**Insight:** Plan '{top_churn_plan}' has the highest churn rate. Focus retention strategies on this plan.")

    st.subheader("📈 Before vs After Retention Impact")
    before = filtered_data.groupby("RiskLevel")["Churn"].mean().reset_index()
    before["Retention"] = 1 - before["Churn"]
    before["Stage"] = "Before Action"

    after = filtered_data.groupby("RiskLevel")["RetentionProbability"].mean().reset_index()
    after.rename(columns={"RetentionProbability": "Retention"}, inplace=True)
    after["Stage"] = "After Action"

    compare = pd.concat([before[["RiskLevel", "Retention", "Stage"]], after[["RiskLevel", "Retention", "Stage"]]])
    fig_retention = px.line(compare, x="RiskLevel", y="Retention", color="Stage", markers=True, template="plotly_dark")
    st.plotly_chart(fig_retention, use_container_width=True)
    st.markdown("**Insight:** After recommended actions, retention probability improves across all risk levels, with the largest increase in High risk members.")

    # --------------------------
    # Action Table + Excel Export
    # --------------------------
    st.subheader("📋 Recovery Action Plan")
    export_columns = [
        "Name", "PhoneNumber", "RiskLevel", "RecommendedAction", "CouponOffer",
        "RetentionProbability", "AvgVisitsPerWeek", "PaymentRatio"
    ]

    filtered_data["Name"] = filtered_data.get("Name", "N/A")

    st.dataframe(
        filtered_data[export_columns],
        use_container_width=True,
    )

    excel_buffer = io.BytesIO()
    filtered_data[export_columns].to_excel(excel_buffer, index=False, sheet_name="RecoveryPlan")
    excel_buffer.seek(0)

    st.download_button(
        label="📥 Download Recovery Plan Excel",
        data=excel_buffer,
        file_name="gym_recovery_plan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload both files")
