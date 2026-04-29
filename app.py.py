import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, date




conn = sqlite3.connect("dashboard.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cases (
    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT,
    assigned_to TEXT,
    status TEXT,
    created_at TEXT,
    completed_at TEXT
)
""")

df = pd.read_sql_query("SELECT * FROM cases", conn)

df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
df['completed_at'] = pd.to_datetime(df['completed_at'], errors='coerce')

today = pd.to_datetime(date.today())

completed_today = df[
    (df['status'] == 'completed') &
    (df['completed_at'].dt.date == today.date())
]

pending_df = df[df['status'] == 'pending']

completed_df = df[df['status'] == 'completed'].copy()
completed_df['processing_days'] = (
    completed_df['completed_at'] - completed_df['created_at']
).dt.days

avg_time = round(completed_df['processing_days'].mean(), 2) if not completed_df.empty else 0

pending_by_emp = pending_df.groupby('assigned_to').size()
completed_by_emp = completed_df.groupby('assigned_to').size()

st.title("Credentialing Dashboard")

st.metric("Cases Today", len(completed_today))
st.metric("Pending", len(pending_df))
st.metric("Avg Time", avg_time)

st.bar_chart(completed_by_emp)
st.bar_chart(pending_by_emp)

st.dataframe(df)

st.subheader("Add Case")

with st.form("form"):
    p = st.text_input("Provider")
    e = st.text_input("Employee")
    s = st.selectbox("Status", ["pending", "completed"])
    submit = st.form_submit_button("Add")

    if submit:
        now = datetime.now()
        comp = now if s == "completed" else None

        cursor.execute(
            "INSERT INTO cases (provider_name, assigned_to, status, created_at, completed_at) VALUES (?, ?, ?, ?, ?)",
            (p, e, s, now, comp)
        )
        conn.commit()
        st.success("Added")

        st.download_button("Download Data", df.to_csv(index=False), "data.csv")