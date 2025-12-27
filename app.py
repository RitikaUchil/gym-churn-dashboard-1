import streamlit as st
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Gym Dashboard", layout="wide")

# ---------------- CSS (VISIBLE & SAFE) ----------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
}

/* KPI container */
.kpi-wrap {
    display: flex;
    justify-content: space-around;
    margin-top: 30px;
}

/* CIRCULAR KPI */
.kpi-circle {
    width: 180px;
    height: 180px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-family: Arial;
    color: white;
    font-weight: bold;
    box-shadow: 0 0 35px rgba(0,0,0,0.9);
}

/* COLORS */
.blue {
    background: radial-gradient(circle at top, #1e90ff, #003366);
    box-shadow: 0 0 30px #1e90ff;
}

.red {
    background: radial-gradient(circle at top, #ff4d4d, #7a0000);
    box-shadow: 0 0 35px #ff4d4d;
    animation: pulse 1.5s infinite;
}

.green {
    background: radial-gradient(circle at top, #2ecc71, #0b6623);
    box-shadow: 0 0 30px #2ecc71;
}

.purple {
    background: radial-gradient(circle at top, #9b59b6, #3b1c4a);
    box-shadow: 0 0 30px #9b59b6;
}

/* Pulse animation */
@keyframes pulse {
    0% { box-shadow: 0 0 15px #ff4d4d; }
    50% { box-shadow: 0 0 45px #ff4d4d; }
    100% { box-shadow: 0 0 15px #ff4d4d; }
}

.kpi-value {
    font-size: 46px;
}

.kpi-label {
    font-size: 14px;
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("🏋️ Gym Owner Dashboard")

# ---------------- DUMMY DATA (SO IT ALWAYS SHOWS) ----------------
data = pd.DataFrame({
    "members": [120],
    "high_risk": [28],
    "avg_visits": [6.4],
    "payment_ratio": [0.82]
})

# ---------------- KPI DISPLAY ----------------
st.markdown(f"""
<div class="kpi-wrap">

  <div class="kpi-circle blue">
    <div class="kpi-value">{data.members[0]}</div>
    <div class="kpi-label">Total Members</div>
  </div>

  <div class="kpi-circle red">
    <div class="kpi-value">{data.high_risk[0]}</div>
    <div class="kpi-label">High Risk</div>
  </div>

  <div class="kpi-circle green">
    <div class="kpi-value">{data.avg_visits[0]}</div>
    <div class="kpi-label">Avg Visits</div>
  </div>

  <div class="kpi-circle purple">
    <div class="kpi-value">{data.payment_ratio[0]}</div>
    <div class="kpi-label">Payment Ratio</div>
  </div>

</div>
""", unsafe_allow_html=True)
