🏋️ Gym Churn Prediction & Retention Dashboard

Retention Intelligence Pro with ML Insights & Excel Export

<!-- Replace with actual screenshot -->

Project Overview

This project is a Gym Owner Dashboard built with Streamlit that predicts member churn using Machine Learning (Random Forest) and provides actionable insights to improve retention.

Predicts churn probability for each member.

Classifies members into High, Medium, Low Risk based on ML predictions.

Suggests personalized retention actions and coupon offers.

Provides interactive visualizations (Plotly charts) to monitor engagement, payments, and risk levels.

Allows Excel export of recovery action plans.

Features

ML-Powered Churn Prediction

Random Forest Classifier predicts likelihood of churn.

Converts predictions into risk levels: High, Medium, Low.

Member Engagement Metrics

Average visits per week

Payment ratio

Insights & Visualizations

Risk distribution (Donut chart)

Avg visits per week (Box plot)

Payment ratio behavior (Violin plot)

Churn intensity by plan (Bar chart)

Before vs After retention impact (Line chart)

Recovery Action Plan

Personalized recommendations

Coupon offers

Downloadable Excel sheet

Installation

Clone the repository:

git clone https://github.com/YourUsername/gym-churn-dashboard-1.git
cd gym-churn-dashboard-1


Install dependencies:

pip install -r requirements.txt

Usage

Run the Streamlit app:

streamlit run app.py


Upload your Members Excel and Attendance Excel files.

Dashboard automatically:

Calculates member metrics

Predicts churn probability using ML

Shows interactive charts and recovery actions

Download Recovery Plan Excel for follow-ups.

Machine Learning Model

Model: Random Forest Classifier

Features Used:

Membership duration (MembershipWeeks)

Average visits per week (AvgVisitsPerWeek)

Payment ratio (PaymentRatio)

Plan Name (PlanName)

Plan Status (PlanStatus)

Target: Churn (1 = churned, 0 = active)

Outputs Churn Probability → mapped to RiskLevel.
