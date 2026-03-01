import streamlit as st

# -----------------------------
# Helper functions (from your code)
# -----------------------------

def time_to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m

def average_wake_up(day_logs):
    times = [time_to_min(day["wake_up"]) for day in day_logs]
    if not times:
        return 0
    return sum(times) / len(times)

def get_peak_hrs(average_wake_mins):
    peak_start = average_wake_mins + 3 * 60
    peak_end   = average_wake_mins + 6 * 60
    return (peak_start, peak_end)

def detect_actual_peak(hourly_avg):
    if not hourly_avg:
        return None
    return max(hourly_avg, key=hourly_avg.get)

def performance_score(session):
    duration_score = session["optimal_duration"] / session["actual_duration"]
    energy_score = session["current_energy"] / session["required_energy"]
    mood_score = session["mood"] / 10
    return round((duration_score + energy_score + mood_score) / 3, 2)

def task_diff(task):
    d = task["optimal_duration"]
    e = task["required_energy"]
    if d > 90 and e > 7:
        return "very_hard"
    elif 60 < d <= 90 and 5 < e <= 7:
        return "hard"
    elif 30 < d <= 60 and 3 < e <= 5:
        return "mid"
    else:
        return "easy"

# -----------------------------
# Main App State
# -----------------------------

tasks = []
day_logs = []

# -----------------------------
# Streamlit UI
# -----------------------------

st.title("Axio: Daily Performance Tracker")

# ---- User Profile ----
st.header("Create User Profile")
age = st.number_input("How old are you?", min_value=0, max_value=120)
wake_up = st.text_input("Typical wake up time (HH:MM)")
sleep_time = st.text_input("Typical sleep time (HH:MM)")
conditions = st.text_input("Medical conditions (comma-separated)")

if st.button("Save Profile"):
    profile = {
        "age": age,
        "wake_up": wake_up,
        "sleep": sleep_time,
        "conditions": [c.strip() for c in conditions.split(",")] if conditions else []
    }
    st.session_state['profile'] = profile
    st.success("Profile saved!")

# ---- Add a New Task ----
st.header("Add a Task")
task_name = st.text_input("Task name")
optimal_duration = st.number_input("Optimal duration (minutes)", min_value=1)
required_energy = st.number_input("Required energy (1-10)", min_value=1, max_value=10)

if st.button("Add Task"):
    task = {
        "id": len(tasks) + 1,
        "name": task_name,
        "optimal_duration": optimal_duration,
        "required_energy": required_energy,
    }
    task["difficulty"] = task_diff(task)
    tasks.append(task)
    st.success(f"Task '{task_name}' added!")

# ---- Start New Day ----
st.header("Start a New Day")
if 'profile' in st.session_state:
    date = st.date_input("Date")
    wake_time = st.text_input("Wake up time (HH:MM)", key="wake_input")
    sleep_last_night = st.text_input("Sleep time last night (HH:MM)", key="sleep_input")

    if st.button("Add Day"):
        rec_hours = 8  # simplified: you can compute from age if you want
        day = {
            "date": str(date),
            "wake_up": wake_time,
            "sleep_time": sleep_last_night,
            "recommended_sleep": rec_hours,
            "sessions": []
        }
        day_logs.append(day)
        st.success(f"Day {date} added!")

# ---- Log a Session ----
st.header("Log a Task Session")
if day_logs and tasks:
    day_select = st.selectbox("Select Day", [d["date"] for d in day_logs])
    task_select = st.selectbox("Select Task", [t["name"] for t in tasks])
    actual_duration = st.number_input("Actual duration (minutes)", min_value=1)
    current_energy = st.slider("Current energy (1-10)", min_value=1, max_value=10)
    mood = st.slider("Mood (1-10)", min_value=1, max_value=10)
    notes = st.text_area("Notes")

    if st.button("Log Session"):
        day = next(d for d in day_logs if d["date"] == day_select)
        task = next(t for t in tasks if t["name"] == task_select)
        session = {
            "task_id": task["id"],
            "task_name": task["name"],
            "optimal_duration": task["optimal_duration"],
            "required_energy": task["required_energy"],
            "actual_duration": actual_duration,
            "current_energy": current_energy,
            "mood": mood,
            "notes": notes,
            "start_time": "00:00",  # simplified
            "end_time": "00:00"
        }
        day["sessions"].append(session)
        st.success(f"Session for '{task_select}' logged!")

# ---- Weekly Summary ----
st.header("Weekly Summary")
if st.button("Show Summary"):
    if day_logs:
        st.subheader("Days Logged")
        for day in day_logs:
            st.write(f"Date: {day['date']}, Sessions: {len(day['sessions'])}")
    else:
        st.write("No days logged yet.")
