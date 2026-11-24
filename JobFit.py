from datetime import date, time, timedelta
from itertools import combinations

import streamlit as st

# Each fictional offer ends with its estimated take-home pay.

# Fictional offers
# In a future version, employers could post and update their listings through an online form, and the app would display the changes automatically.

OFFERS = [
    ("Event welcome desk", "Campus Events", "Campus", 3, "09:00", "17:00", 110),
    ("Babysitting", "Campus Family", "Near campus", 5, "14:15", "17:45", 65),
    ("Online tutoring", "Study Club", "Remote", 2, "15:00", "17:00", 45),
    ("Library shelving", "Campus Library", "Campus", 3, "14:00", "16:00", 26),
    ("Café shift", "Square Café", "Near campus", 4, "17:00", "20:00", 39),
    ("Sports desk", "Campus Sports", "Campus", 5, "10:00", "13:00", 42),
    ("Stock count", "Local Bookshop", "City centre", 6, "10:00", "12:30", 35),
    ("Workshop setup", "Student Arts Club", "Campus", 0, "18:00", "20:00", 25),
    ("Market stall", "Local Market", "City centre", 6, "08:00", "12:00", 55),
    ("Research session", "Campus Lab", "Campus", 1, "17:30", "18:30", 18),
]
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def minutes_since_midnight(clock):
    return clock.hour * 60 + clock.minute


def build_catalog():
    jobs = []
    for title, employer, location, day, start, end, pay in OFFERS:
        day_offset = day * 24 * 60
        shift_start = day_offset + minutes_since_midnight(time.fromisoformat(start))
        shift_end = day_offset + minutes_since_midnight(time.fromisoformat(end))
        jobs.append({
            "title": title, "employer": employer, "location": location,
            "shift": f"{DAYS[day][:3]} {start}–{end}",
            "shift_start": shift_start, "shift_end": shift_end,
            "pay": pay,
            "minutes": shift_end - shift_start,
        })
    return sorted(jobs, key=lambda job: job["shift_start"])


def find_plan(jobs, target, max_minutes):
    plans = [((), 0, 0)]
    for count in range(1, len(jobs) + 1):
        for group in combinations(jobs, count):
            minutes = sum(job["minutes"] for job in group)
            if minutes > max_minutes:
                continue
            if any(first["shift_end"] > second["shift_start"] for first, second in zip(group, group[1:])):
                continue
            plans.append((group, sum(job["pay"] for job in group), minutes))
    meeting_target = [plan for plan in plans if plan[1] >= target]
    if meeting_target:
        return min(meeting_target, key=lambda plan: (plan[2], -plan[1], len(plan[0])))
    return min(plans, key=lambda plan: (-plan[1], plan[2], len(plan[0])))


def duration(minutes):
    hours, remaining = divmod(minutes, 60)
    return f"{hours} h {remaining:02d}" if remaining else f"{hours} h"


def render():
    st.set_page_config(page_title="JobFit Campus", page_icon="📅", layout="wide")
    st.title("JobFit Campus")
    st.write("Find student jobs that fit your week and your income goal.")
    st.caption("Classroom prototype with fictional campus offers. Earnings are estimates.")
    with st.sidebar:
        st.header("Your week")
        selected = st.date_input("Choose any day in your planning week", value=date.today())
        monday = selected - timedelta(days=selected.weekday())
        st.caption(f"Week beginning {monday:%d %b %Y}")
        target = st.number_input("Income goal (€)", 1, 10000, 100, step=5)
        hours = st.number_input("Maximum work hours this week", 0.0, 168.0, 6.0, step=0.5)
        active_days = st.multiselect("Days you can work", DAYS, default=["Wednesday", "Saturday"])
        availability = []
        for day in active_days:
            st.markdown(f"**{day}**")
            a, b = st.columns(2)
            start = a.time_input("From", time(14), key=f"{day}_start")
            end = b.time_input("Until", time(18), key=f"{day}_end")
            if end <= start:
                st.error(f"{day} needs an end time after its start time.")
                continue
            day_offset = DAYS.index(day) * 24 * 60
            availability.append((day_offset + minutes_since_midnight(start),
                                 day_offset + minutes_since_midnight(end)))

    jobs = build_catalog()
    matching = [
        job for job in jobs
        if any(start <= job["shift_start"] and job["shift_end"] <= end for start, end in availability)
    ]
    plan, earnings, minutes = find_plan(matching, target, round(hours * 60))

    st.header("Your suggested plan")
    if earnings >= target:
        st.success("This plan meets your goal in the least time.")
    else:
        st.info(f"Best available result under your constraints. You are €{target - earnings:,} short of your goal.")
    a, b, c = st.columns(3)
    a.metric("Estimated earnings", f"€{earnings:,}")
    b.metric("Total work time", duration(minutes))
    c.metric("Missions in your plan", len(plan))
    for job in plan:
        st.markdown(f"**{job['title']}** · {job['employer']}")
        st.write(f"{job['shift']} · {job['location']} · €{job['pay']}")

    st.header("Compatible offers")
    st.caption("These offers fit your daily time windows. The suggested plan also respects your total hours limit.")
    if matching:
        st.dataframe([{
            "Mission": job["title"], "Employer": job["employer"], "Location": job["location"],
            "Shift": f"{job['shift']}",
        } for job in matching], hide_index=True)
    else:
        st.write("No offer fits the selected time windows. Change a day or time to explore the catalog.")
    with st.expander("View all fictional offers"):
        for job in jobs:
            st.write(f"{job['title']} · {job['shift']} · {job['location']}")


if __name__ == "__main__":
    render()
