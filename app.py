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
today = date.today()
scheduler = Scheduler(owner)

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
    st.dataframe(
        [{"Name": p.name, "Species": p.species, "Breed": p.breed, "Age": p.age, "Tasks": len(p.tasks)}
         for p in owner.pets],
        hide_index=True,
        width="stretch",
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

    if owner.get_all_tasks():
        # Filters use Scheduler.filter_tasks(); None means "don't filter on this".
        col1, col2 = st.columns(2)
        with col1:
            pet_filter = st.selectbox("Show tasks for", ["All pets"] + [p.name for p in owner.pets])
        with col2:
            status_filter = st.radio("Status", ["All", "To do", "Done"], horizontal=True)
        shown = scheduler.filter_tasks(
            pet_name=None if pet_filter == "All pets" else pet_filter,
            completed={"All": None, "To do": False, "Done": True}[status_filter],
        )
        if shown:
            st.dataframe(
                [
                    {
                        "Pet": t.pet_name,
                        "Task": t.title,
                        "Minutes": t.duration_minutes,
                        "Priority": t.priority,
                        "When": t.fixed_time or t.preferred_time or "any",
                        "Repeats": t.frequency,
                        "Due": "-" if t.is_complete()
                        else "now" if t.due_date is None or t.due_date <= today
                        else f"{t.due_date:%a %b %d}",
                        "Status": "✅ Done" if t.is_complete() else "To do",
                    }
                    for t in shown
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("No tasks match these filters.")

        # Completing a task uses Scheduler.mark_task_complete(), which also creates the next occurrence.
        open_tasks = scheduler.filter_tasks(completed=False)
        if open_tasks:
            with st.form("complete_task"):
                labels = {t.task_id: f"{t.pet_name}: {t.title}" for t in open_tasks}
                chosen_id = st.selectbox("Mark a task done", list(labels), format_func=labels.get)
                if st.form_submit_button("Mark complete"):
                    next_task = scheduler.mark_task_complete(chosen_id, today)
                    st.success(
                        f"Nice! {labels[chosen_id]} is done. The next one is due "
                        f"{next_task.due_date:%A, %B %d} ({next_task.frequency})."
                    )
    else:
        st.info("No tasks yet. Add one above.")

# --- Schedule ----------------------------------------------------------------
st.divider()
st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    st.session_state.show_plan = True

# Once shown, the plan is rebuilt on every rerun so it stays current as tasks change.
if st.session_state.get("show_plan"):
    scheduler.generate_plan(today)
    conflicts = scheduler.find_conflicts()
    used = sum(s.task.duration_minutes for s in scheduler.plan)

    col1, col2, col3 = st.columns(3)
    col1.metric("Tasks scheduled", len(scheduler.plan))
    col2.metric("Time used", f"{used} / {owner.available_minutes} min")
    col3.metric("Conflicts", len(conflicts))

    # Conflicts come first: two things at once is the problem the owner most needs to fix.
    for first, second in conflicts:
        st.error(
            f"⚠️ **{first.task.pet_name}'s {first.task.title}** "
            f"({first.time}-{first.end:%H:%M}) overlaps **{second.task.pet_name}'s {second.task.title}** "
            f"({second.time}-{second.end:%H:%M}). You can't do both at once - change one task's "
            f"exact time, or clear it so PawPal+ can find a free slot."
        )

    if scheduler.plan:
        in_conflict = {s.task.task_id for pair in conflicts for s in pair}
        st.caption("Sorted by start time.")
        st.dataframe(
            [
                {
                    "Time": f"{s.time}-{s.end:%H:%M}",
                    "Pet": s.task.pet_name,
                    "Task": s.task.title,
                    "Priority": s.task.priority,
                    "Why": s.reason,
                    "": "⚠️ conflict" if s.task.task_id in in_conflict else "",
                }
                for s in scheduler.sort_by_time(scheduler.plan)
            ],
            hide_index=True,
            width="stretch",
        )
        if not conflicts:
            st.success(f"All set! {len(scheduler.plan)} tasks fit in your day with no overlaps.")
    else:
        st.info("Nothing to schedule today. Add tasks, or check that they aren't already done.")

    if scheduler.skipped:
        st.warning(
            "**Didn't fit today:**\n"
            + "\n".join(f"- {t.pet_name}: {t.title} ({t.priority} priority) - {reason}" for t, reason in scheduler.skipped)
        )

    with st.expander("Full explanation"):
        st.text(scheduler.explain_plan())
