import streamlit as st
import json
from datetime import date
from openai import OpenAI
from streamlit_calendar import calendar
import pandas as pd
import os
import hashlib
import os
import json
import streamlit as st

USERS_FILE = "users.json"


# Loading exi sting data
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()




# Only show login/register form if user not logged in
if "user" not in st.session_state or not st.session_state.user:
    st.title("Axio Login / Register")
    mode = st.radio("Choose mode", ["Login", "Register"], key="login_mode")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button(mode, key="login_button"):
        if not username or not password:
            st.warning("Enter both username and password")
        else:
            if mode == "Register":
                if username in users:
                    st.error("Username already exists")
                else:
                    users[username] = hash_password(password)
                    with open(USERS_FILE, "w") as f:
                        json.dump(users, f, indent=4)
                    st.success("Registered! You can now login")
            else:  # Login
                if username not in users:
                    st.error("User not found")
                elif users[username] != hash_password(password):
                    st.error("Incorrect password")
                else:
                    st.session_state.user = username
                    st.success(f"Logged in as {username}")
                    st.rerun()
else:
    st.write(f"Logged in as: {st.session_state.user}")  


if "user" not in st.session_state:
    st.stop()

client = OpenAI()

st.set_page_config(page_title="Axio", layout="wide")

st.markdown("""
<style>
.main {
    background-color: #0f1117;
}
h1, h2, h3 {
    color: white;
}
.stButton>button {
    border-radius: 10px;
    background-color: #6366f1;
    color: white;
}
</style>
""", unsafe_allow_html=True)



user_file = f"{st.session_state.user}_data.json"

#load user data
if "profile" not in st.session_state:
    st.session_state.profile = {}
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "day_logs" not in st.session_state:
    st.session_state.day_logs = []

try:
    with open(user_file, "r") as f:
        user_data = json.load(f)
        st.session_state.profile = user_data.get("profile", st.session_state.profile)
        st.session_state.tasks = user_data.get("tasks", st.session_state.tasks)
        st.session_state.day_logs = user_data.get("day_logs", st.session_state.day_logs)
except:
    pass

st.session_state.day_logs = [
    d for d in st.session_state.day_logs if isinstance(d, dict) and "date" in d
]

def save_user_data():
    with open(user_file, "w") as f:
        json.dump({
            "profile": st.session_state.profile,
            "tasks": st.session_state.tasks,
            "day_logs": st.session_state.day_logs
        }, f, indent=4)

def compute_duration(start, end):
    s = start.hour * 60 + start.minute
    e = end.hour * 60 + end.minute
    if e < s:
        e += 24 * 60
    return max(1, e - s)

def performance_score(s):
    if s.get("actual_duration",0) == 0:
        return 0
    return round((
        min(s["actual_duration"] / s["optimal_duration"], 1) +
        (s["current_energy"] / s["required_energy"]) +
        (s["mood"] / 10)
    ) / 3, 2)

def analyze_hourly_performance(day_logs):
    hourly = {}
    for d in day_logs:
        for s in d.get("sessions", []):
            hour = int(s["start_time"].split(":")[0])

            base_score = (
                (s["current_energy"] / s["required_energy"]) +
                (s["mood"] / 10)
            ) / 2

            hourly.setdefault(hour, []).append(base_score)

    return {h: sum(v)/len(v) for h, v in hourly.items()}

def performance_label(score):
    if score >= 0.85:
        return "Peak Focus"
    elif score >= 0.7:
        return "Highly Productive"
    elif score >= 0.55:
        return "Solid"
    elif score >= 0.4:
        return "Low Energy"
    else:
        return "Not Ideal"

def detect_actual_peak(hourly):
    return max(hourly, key=hourly.get) if hourly else None

def analyze_energy_mismatch(day_logs):
    mismatches=[]
    for day in day_logs:
        for s in day.get("sessions",[]):
            gap= s["required_energy"] - s["current_energy"]
            if gap >=3:
                mismatches.append({
                    "task": s["task_name"],
                    "gap": gap,
                    "date": day.get("date", "Unknown")
                })
    return mismatches

def analyze_task_sequence(day_logs):
    sequences = []
    for day in day_logs:
        sessions = day.get("sessions", [])
        for i in range(len(sessions)-1):
            first = sessions[i]
            second = sessions[i+1]
            change = performance_score(second) - performance_score(first)
            sequences.append({
                "pair": (first["task_name"], second["task_name"]),
                "change": change
            })
    return sequences

def get_today_sessions():
    today = str(date.today())
    for d in st.session_state.day_logs:
        if d.get("date") == today:
            return d.get("sessions", [])
    return []

st.sidebar.title(" Axio")
menu = st.sidebar.radio("Navigate", ["Dashboard","Log Session","Tasks","Profile","AI Coach"])

if menu == "Dashboard":
    st.title("Axio Overview")

    events= []
    for d in st.session_state.day_logs:
        for s in d.get("sessions",[]):
            events.append({
                "title": s["task_name"],
                "start": f"{d['date']}T{s['start_time']}",
                "end": f"{d['date']}T{s['end_time']}"
            })
    calendar(events=events)

    hourly = analyze_hourly_performance(st.session_state.day_logs)
    peak = detect_actual_peak(hourly)
    scores = [performance_score(s) for d in st.session_state.day_logs for s in d.get("sessions",[])]

    col1, col2 = st.columns(2)
    col1.metric("Peak Hour", f"{peak}:00" if peak else "N/A")
    col2.metric("Sessions Logged", len(scores))

    st.subheader("Recommended Sleep Window")

    age = st.session_state.profile.get("age", None)

    if age:
        if age <= 18:
            sleep_range = "8–10 hours"
        elif age <= 25:
            sleep_range = "7–9 hours"
        elif age <= 64:
            sleep_range = "7–8 hours"
        else:
            sleep_range = "7–9 hours"

        wake = st.session_state.profile.get("wake")
        sleep = st.session_state.profile.get("sleep")

        if wake and sleep:
            st.success(f"Ideal: {sleep_range} | Your schedule: {sleep} → {wake}")
        else:
            st.info(f"Ideal for your age: {sleep_range}")
    else:
        st.info("Add your age in Profile")

    st.divider()
    st.subheader("Today's Sessions")

    sessions = get_today_sessions()
    if sessions:
        for s in sessions:
            st.write(f"**{s['task_name']}** | {s['start_time']} → {s['end_time']}")
    else:
        st.info("No sessions today")

    st.divider()
    st.subheader("Your Daily Rhythm")

    if hourly:
        sorted_hours = sorted(hourly.items(), key=lambda x: x[1], reverse=True)
        for h, score in sorted_hours:
            st.write(f"{h}:00 → {performance_label(score)}")
    else:
        st.info("No data yet")

    st.subheader("⚠️ Energy Mismatches ⚠️")
    mismatches= analyze_energy_mismatch(st.session_state.day_logs)
    if not scores:
        st.info("No data yet")
    elif mismatches:
        for m in mismatches[-5:]:
            st.warning(f"{m['task']} | gap: {m['gap']} | {m['date']}")
    else:
        st.success("Great energy alignment")

elif menu == "Log Session":
    st.title(" Log Session")
    if not st.session_state.tasks:
        st.warning("Create a task first")
    else:
        task_name = st.selectbox("Task", [t["name"] for t in st.session_state.tasks])
        task = next(t for t in st.session_state.tasks if t["name"]==task_name)
        start = st.time_input("Start Time")
        end = st.time_input("End Time")
        energy = st.slider("Energy BEFORE task",1,10)
        mood = st.slider("Mood BEFORE task",1,10)

        if st.button("Log Session"):
            duration = compute_duration(start,end)
            today = str(date.today())
            day = next((d for d in st.session_state.day_logs if d.get("date") == today),None)
            if not day:
                day={"date":today,"sessions":[]}
                st.session_state.day_logs.append(day)

            day["sessions"].append({
                "task_name": task["name"],
                "start_time": str(start),
                "end_time": str(end),
                "actual_duration": duration,
                "optimal_duration": task["optimal_duration"],
                "required_energy": task["required_energy"],
                "current_energy": energy,
                "mood": mood
            })
            save_user_data()
            st.success("Session logged!")

elif menu == "Tasks":
    st.title("Tasks")

    with st.form("task_form"):
        name = st.text_input("Task Name")
        optimal = st.number_input("Optimal Duration (min)",1)
        energy = st.slider("Energy Required",1,10)

        if st.form_submit_button("Add Task"):
            st.session_state.tasks.append({
                "id": len(st.session_state.tasks)+1,
                "name": name,
                "optimal_duration": optimal,
                "required_energy": energy
            })
            save_user_data()
            st.success("Task added!")

    st.subheader("Your Tasks")

    for i, t in enumerate(st.session_state.tasks):
        col1, col2, col3 = st.columns([3,1,1])
        col1.write(f"• {t['name']}")

        if col2.button("Edit", key=f"edit_{i}"):
            st.session_state.edit_index = i

        if col3.button("Delete", key=f"del_{i}"):
            st.session_state.tasks.pop(i)
            save_user_data()
            st.experimental_rerun()

    if "edit_index" in st.session_state:
        idx = st.session_state.edit_index
        task = st.session_state.tasks[idx]

        new_name = st.text_input("Task Name", value=task["name"])
        new_optimal = st.number_input("Optimal Duration (min)", value=task["optimal_duration"])
        new_energy = st.slider("Energy Required",1,10, value=task["required_energy"])

        if st.button("Save Changes"):
            task["name"] = new_name
            task["optimal_duration"] = new_optimal
            task["required_energy"] = new_energy
            save_user_data()
            del st.session_state.edit_index
            st.experimental_rerun()

elif menu == "Profile":
    st.title("👤 Profile")

    with st.form("profile_form"):
        age = st.number_input("Age", value=st.session_state.profile.get("age",25))
        wake = st.time_input("Wake-up Time")
        sleep = st.time_input("Sleep Time")

        if st.form_submit_button("Save"):
            st.session_state.profile={"age":age,"wake":str(wake),"sleep":str(sleep)}
            save_user_data()
            st.success("Saved!")
