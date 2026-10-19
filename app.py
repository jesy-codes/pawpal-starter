from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' care for the day, based on your time and each task's priority.")

# st.session_state survives reruns, so the Owner (and its pets and tasks) is only created once.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=90)
owner: Owner = st.session_state.owner

# --- Owner -------------------------------------------------------------------
st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.set_available_time(
        int(st.number_input("Minutes available today", min_value=0, max_value=1440, value=owner.available_minutes))
    )

# --- Pets --------------------------------------------------------------------
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        breed = st.text_input("Breed (optional)")
    with col4:
        age = st.number_input("Age", min_value=0, max_value=40, value=0)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Please enter a pet name.")
        else:
            try:
                owner.add_pet(Pet(pet_name.strip(), species, breed=breed.strip(), age=int(age)))
                st.success(f"Added {pet_name.strip()}.")
            except ValueError as e:
                st.error(str(e))

if owner.pets:
    st.table(
        [{"Name": p.name, "Species": p.species, "Breed": p.breed, "Age": p.age, "Tasks": len(p.tasks)}
         for p in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

# --- Tasks -------------------------------------------------------------------
st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet first, then you can give it care tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            pet_choice = st.selectbox("For pet", [p.name for p in owner.pets])
            task_title = st.text_input("Task title", placeholder="Morning walk")
            category = st.selectbox("Category", ["walk", "feeding", "meds", "grooming", "enrichment", "general"])
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            preferred = st.selectbox("Time of day", ["any", "morning", "afternoon", "evening"])
            fixed = st.text_input("Exact time (optional)", placeholder="HH:MM, e.g. 08:00")
        frequency = st.radio("Repeats", ["daily", "weekly"], horizontal=True)
        if st.form_submit_button("Add task"):
            if not task_title.strip():
                st.error("Please enter a task title.")
            else:
                pet = next(p for p in owner.pets if p.name == pet_choice)
                try:
                    task = Task(
                        task_title.strip(),
                        int(duration),
                        priority,
                        category=category,
                        preferred_time=None if preferred == "any" else preferred,
                        fixed_time=fixed.strip() or None,
                        frequency=frequency,
                    )
                except ValueError as err:
                    st.error(str(err))
                else:
                    pet.add_task(task)
                    st.success(f"Added '{task_title.strip()}' for {pet.name}.")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.table(
            [
                {
                    "Pet": t.pet_name,
                    "Task": t.title,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                    "Time of day": t.fixed_time or t.preferred_time or "any",
                    "Repeats": t.frequency,
                }
                for t in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

# --- Schedule ----------------------------------------------------------------
st.divider()
st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner)
    scheduler.generate_plan(date.today())
    if scheduler.plan:
        st.table(
            [
                {
                    "Time": s.time,
                    "Pet": s.task.pet_name,
                    "Task": s.task.title,
                    "Minutes": s.task.duration_minutes,
                    "Why": s.reason,
                }
                for s in scheduler.plan
            ]
        )
    else:
        st.warning("Nothing could be scheduled. Add tasks or increase your available time.")
    for warning in scheduler.detect_conflicts():
        st.error(f"Conflict: {warning}")
    for t, reason in scheduler.skipped:
        st.warning(f"Skipped {t.pet_name}: {t.title} - {reason}")
    with st.expander("Full explanation"):
        st.text(scheduler.explain_plan())
