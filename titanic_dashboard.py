import pandas as pd
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# ------------------------
# Step 1: Extract
# ------------------------
url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
df = pd.read_csv(url)

# ------------------------
# Step 2: Transform
# ------------------------
df['Age'] = df['Age'].fillna(df['Age'].mean())
df['Cabin'] = df['Cabin'].fillna("Unknown")

# ------------------------
# Step 3: Load (SQLite)
# ------------------------
conn = sqlite3.connect("etl_demo.db")
df.to_sql("titanic_passengers", conn, if_exists="replace", index=False)

# ------------------------
# Step 4: Dashboard
# ------------------------
st.title("🚢 Titanic Survival Dashboard")

# Gender-wise survival
query1 = "SELECT Sex, AVG(Survived)*100 as survival_rate FROM titanic_passengers GROUP BY Sex;"
gender_survival = pd.read_sql(query1, conn)

st.subheader("🔹 Survival Rate by Gender")
st.bar_chart(gender_survival.set_index("Sex"))

# Class-wise survival
query2 = "SELECT Pclass, AVG(Survived)*100 as survival_rate FROM titanic_passengers GROUP BY Pclass;"
class_survival = pd.read_sql(query2, conn)

st.subheader("🔹 Survival Rate by Passenger Class")
st.bar_chart(class_survival.set_index("Pclass"))

# Overall survival distribution
st.subheader("🔹 Overall Survival Distribution")
fig, ax = plt.subplots()
sns.countplot(x="Survived", data=df, palette="viridis", ax=ax)
ax.set_xticklabels(["Did Not Survive", "Survived"])
st.pyplot(fig)

st.success("✅ Dashboard running successfully!")
