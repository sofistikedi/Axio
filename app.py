tasks = []

day_logs=[] #create new day func
def time_to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def average_wake_up(day_logs):
    times = []
    for day in day_logs:
        times.append(time_to_min(day["wake_up"]))

    avg = sum(times) / len(times)
    return avg


def get_peak_hrs(average_wake_mins):
    peak_start = average_wake_mins + 3 * 60
    peak_end   = average_wake_mins + 6 * 60
    return (peak_start, peak_end)

def detect_actual_peak(hourly_avg):  #outside theory,what did user do practically in real life?
    best_hour= max(hourly_avg,key=hourly_avg.get)
    return best_hour


def get_lowest_hrs(average_wake_mins):
    dip_start = average_wake_mins + 9 * 60
    dip_end   = average_wake_mins + 12 * 60
    return (dip_start, dip_end)


def performance_score(session):
    duration_score = session["optimal_duration"] / session["actual_duration"]
    energy_score = session["current_energy"] / session["required_energy"]
    mood_score = session["mood"] / 10

    return round((duration_score + energy_score + mood_score) / 3, 2)
def analyze_hourly_performance(day_logs):
    hourly_data= {}
    for day in day_logs:
        for s in  day["sessions"]:
            hour= int(s["start_time"].split(":")[0])
            score= performance_score(s)
            hourly_data.setdefault(hour, []).append(score)
    hourly_avg={}
    for hour,data in hourly_data.items():
        hourly_avg[hour]= sum(data) / len(data)
    return hourly_avg


def is_in_peak(hours,peak_range):
    return peak_range[0] <= hours <= peak_range[1]


def consistency_score(day_logs):
    wake_times = [time_to_min(d["wake_up"]) for d in day_logs]
    if not wake_times:
        return 0
    variance = max(wake_times) - min(wake_times)
    score = max(0, 1 - (variance / 180))
    return round(score,2)
   



    

def create_user_profile():
    age = int(input("How old are you?: "))
    wake_up = input("When do you typically wake up? (hr:min): ")
    sleep = input("When do you call it a day? (hr:min): ")
    conditions = input("Do you have any medical conditions? (eg. ADHD): ")

    profile = {
        "age": age,
        "wake_up": wake_up,
        "sleep": sleep,
        "conditions": [c.strip() for c in conditions.split(",")] if conditions else []
    }
    return profile

def start_new_day(profile):
    date= input("Today's date:(YYYY-MM-DD)")
    wake_up_time= input("When did you wake up?: (hr:min)")
    sleep_time= input("When did you go to sleep last night?")
    rec= reccomended_sleeping_hours(profile["age"])
    day={"date": date,
        "wake_up": wake_up_time,
        "sleep_time": sleep_time,
        "recommended_sleep": rec,
        "sessions": []}
    day_logs.append(day)
    return day

    

age_sleep_guide = {
    (16, 18): (8, 10),
    (19, 25): (7, 9),
    (26, 40): (7, 9),
    (41, 60): (7, 8),
    (61, 100): (6, 8)
}
cognitive_windows = {
    "low_morning": (0, 1),
    "rising": (1, 3),
    "peak": (3, 6),
    "moderate": (6, 9),
    "dip": (9, 12),
    "evening_recovery": (12, 15)
}


def reccomended_sleeping_hours(age):
    for (low, high), hours in age_sleep_guide.items():
        if low <= age <= high:
            return hours


def create_task():
    name = input("Task name: ")
    optimal = int(input("Optimal duration (minutes): "))
    required_energy = int(input("Required energy (1-10): "))

    task = {
        "id": len(tasks) + 1,
        "name": name,
        "optimal_duration": optimal,
        "required_energy": required_energy
    }
    task["difficulty"] = task_diff(task)


    tasks.append(task)
    print(f"Task '{name}' created.")
    return task
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
def recommend_schedule(tasks, peak_range, dip_range):
    schedule = {"peak": [], "dip": [], "moderate": []}

    for t in tasks:
        if t["difficulty"] in ["hard", "very_hard"]:
            schedule["peak"].append(t["name"])
        elif t["difficulty"] == "easy":
            schedule["dip"].append(t["name"])
        else:
            schedule["moderate"].append(t["name"])

    return schedule
    
    #is the user too tired to start the task in the first place?
def analyze_energy_mismatch(day_logs):
    mismatches = []

    for d in day_logs:
        for s in d["sessions"]:
            gap = s["required_energy"] - s["current_energy"]
            if gap > 3:
                mismatches.append({
                    "task": s["task_name"],
                    "gap": gap,
                    "date": d["date"]
                })

    return mismatches




def analyze_task_sequence (day):                 #are harder tasks easier for the user after easier ones and vice versa
    sessions=day["sessions"]
    sequence=[]
    for i in range(len(sessions)-1):
        first=sessions[i]
        second=sessions[i+1]

        first_score=performance_score(first)
        second_score=performance_score(second)
        sequence.append({
            "pair":(first["task_name"],second["task_name"]),
            "performance_change": second_score - first_score})
    return sequence




def log_session(day,task):
    date = input("Date (YYYY-MM-DD): ")
    start = input("What time did you start? (hr:min): ")
    end = input("When did you finish? (hr:min): ")
    actual_duration = int(input("Actual duration (minutes): "))
    current_energy = int(input("What would you rate your energy on a scale of 1 to 10?: "))
    mood = int(input("How are you feeling on a scale of 1 to 10?: "))
    note = input("Anything you would like to add?: ")

    session = {
        "task_id": task["id"],
        "task_name": task["name"],
        "optimal_duration": task["optimal_duration"],
        "required_energy": task["required_energy"],
        "date": date,
        "start_time": start,
        "end_time": end,
        "actual_duration": actual_duration,
        "current_energy": current_energy,
        "mood": mood,
        "notes": note
    
    }
    day["sessions"].append(session)


def daily_summary(date):
    for day in day_logs:
        if day["date"] == date:
            for s in day["sessions"]:
                diff = s["actual_duration"] - s["optimal_duration"]
                status = "on time" if diff <= 0 else "over time"
                print(f"{s['task_name']} : {status}, Mood: {s['mood']}, Energy: {s['current_energy']}")


def check_overlaps(day):
    sessions = day["sessions"]
    overlaps = []

    for i in range(len(sessions)):
        for j in range(i + 1, len(sessions)):
            s1 = sessions[i]
            s2 = sessions[j]

            if s1["start_time"] < s2["end_time"] and s2["start_time"] < s1["end_time"]:
                overlaps.append((s1["task_name"], s2["task_name"]))

    return overlaps

def add_feedback(session):
    feedback = []
    if session["actual_duration"] <= session["optimal_duration"]:
        feedback.append("Nice, you are right on time!")
    else:
        feedback.append(f"{session['task_name']} took longer than it should have.")
    return feedback
def weekly_reflection(day_logs):
    hourly= analyze_hourly_performance(day_logs)
    best_hour= detect_actual_peak(hourly)
    consistency=consistency_score(day_logs)
    mismatches= analyze_energy_mismatch(day_logs)
    print("\n----WEEKLY REPORT----")
    print("Best performance hour:", best_hour)
    print("Wake consistency:", consistency)
    print("Energy mismatches:", len(mismatches))
    

def add_feedback(session,day,previous_session,peak_range,dip_range):
    feedback=[]
    start_h= peak_range[0] // 60
    start_m= peak_range[0] % 60
    end_h= peak_range[1] // 60
    end_m= peak_range[1] % 60
    easy_tasks = easy_tasks = [s["task_name"] for s in day["sessions"] if s["difficulty"] == "easy"]
    start_hour= int(session["start_time"].split(":")[0])
    if not is_in_peak (start_hour*60,peak_range):
        feedback.append("You worked outside your peak window. Try scheduling this task earlier.")
    if session["difficulty"] ["hard", "very hard"] and not is_in_peak(start_hour * 60, peak_range):
       feedback.append(f"This task is demanding, so it should be done during your peak hours. Try scheduling it between {start_h:02d}:{start_m:02d}–{end_h:02d}:{end_m:02d}.")
    if previous_session:
        if previous_session["difficulty"] in ["hard", "very_hard"] and session["difficulty"] in ["hard", "very_hard"] :
            easy_tasks= [s["task_name"] for s in day["sessions"] if s["difficulty"]== "easy"]
            feedback.append(f"Two demanding tasks back-to-back may have caused cognitive fatigue. Try doing {session['task_name']} after an easy task such as: {easy_tasks}  ")


