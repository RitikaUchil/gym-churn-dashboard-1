import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load cleaned data
df = pd.read_csv("data/processed/gym_members_clean.csv")

# Features & target
X = df.drop("Churn", axis=1)
y = df["Churn"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)
model.fit(X_train, y_train)

# Save model
with open("models/churn_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model trained and saved as churn_model.pkl")
