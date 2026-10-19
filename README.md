# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🧩 Implementation Summary

The core logic lives in `pawpal_system.py` (diagram: `diagrams/uml.mmd`) and is built from five classes:

- **Task** (dataclass): one care activity with a duration, a priority (high/medium/low), an optional time of day (morning/afternoon/evening), an optional exact `fixed_time` ("HH:MM", e.g. for meds), and a frequency (daily/weekly). Completing a task through `Pet.mark_task_complete()` (or `Scheduler.mark_task_complete()`) records the date and adds a new occurrence due the next day (daily) or 7 days later (weekly); `is_due()` skips finished tasks and ones whose due date hasn't arrived. Each task gets a unique id and is checked for invalid values when created or edited.
- **Pet** (dataclass): a pet's details and its list of tasks. `add_task()` links each task to the pet by name, `remove_task()` removes by id, and `mark_task_complete()` completes a task and adds its next occurrence.
- **Owner** (dataclass): the owner's name, the minutes they have available today, and their pets. `get_all_tasks()` returns every pet's tasks in one list.
- **ScheduledTask** (dataclass): one entry in the day's plan, holding the `task`, its `start` time, and the `reason` it was chosen, with `end` and `time` ("HH:MM") worked out from them.
- **Scheduler**: builds one daily plan for the owner as a list of `ScheduledTask`s (`plan`, in start-time order) plus `skipped`, a list of `(task, reason)` pairs. `generate_plan()` reads `owner.get_all_tasks()`, keeps the tasks that are due, and picks them by priority until the owner's time runs out; tasks that don't fit are skipped with a reason. It then gives each chosen task a start time: fixed-time tasks go exactly at their set time, and the rest are laid out from 08:00 (afternoon tasks at 12:00 or later, evening tasks at 18:00 or later), moving past any fixed-time task they would overlap. `sort_by_time()` orders planned tasks by start time, `filter_tasks()` filters by pet and/or completion status, `detect_conflicts()` warns about overlapping tasks, and `explain_plan()` describes why each task was scheduled, skipped, or in conflict.

How they work together: an **Owner** has **Pets**, each **Pet** has **Tasks**, and the **Scheduler** asks the Owner for all tasks so every pet shares the same time budget.

`main.py` builds a sample owner with two pets (tasks added out of order, two meds set for the same time on purpose), completes one task, prints today's schedule, and then prints the sorted and filtered task lists; `tests/test_pawpal.py` holds the tests.

## 🖥️ Sample Output

Output of `python main.py` (one owner, two pets, 90 minutes available). Luna's "Brush coat" was completed first, so it isn't scheduled today and a new one is due tomorrow:

```
Completed 'Brush coat' for Luna; next one due Tuesday, October 20

================================================================
Today's Schedule for Jordan - Monday, October 19, 2026
Time used: 70 of 90 minutes
================================================================
Time   Pet     Task                Length   Priority
----------------------------------------------------------------
08:00  Mochi   Joint supplement    5 min    high
08:00  Luna    Thyroid medication  5 min    high
08:05  Mochi   Breakfast           10 min   high
12:00  Luna    Feather toy play    20 min   medium
18:00  Mochi   Evening walk        30 min   high

Conflicts:
  ! Mochi: Joint supplement (08:00-08:05) overlaps Luna: Thyroid medication (08:00-08:05)

Skipped:
  - Mochi: Bath and brush - not enough time left (needs 45 min, 20 min left)

Why this plan:
  - Joint supplement: high priority, set for 08:00
  - Thyroid medication: high priority, set for 08:00
  - Breakfast: high priority, preferred in the morning
  - Feather toy play: medium priority, preferred in the afternoon
  - Evening walk: high priority, preferred in the evening

Plan, sorted by start time:
  08:00  Luna   Thyroid medication
  08:00  Mochi  Joint supplement
  08:05  Mochi  Breakfast
  12:00  Luna   Feather toy play
  18:00  Mochi  Evening walk

Luna's tasks:
  Luna   Feather toy play    due now
  Luna   Brush coat          done Oct 19
  Luna   Thyroid medication  due now
  Luna   Brush coat          due Oct 20

Completed tasks:
  Luna   Brush coat          done Oct 19
```

(The output also prints the plan reversed before sorting it, and Mochi's tasks still to do. Luna's two "Brush coat" lines are today's completed one and tomorrow's new one.)

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
collected 9 items

tests/test_pawpal.py .........                                           [100%]

============================== 9 passed in 0.05s ===============================
```

The tests cover marking a task complete, adding tasks to a pet, sorting by start time, filtering by pet and completion, daily and weekly recurrence (including month and year rollovers), conflict detection, placing flexible tasks around fixed ones, and rejecting an invalid fixed time.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.generate_plan()`, `Scheduler.sort_by_time()` | Tasks are picked by priority (shorter first on ties so more fit). `sort_by_time()` sorts `ScheduledTask`s with a lambda key on their "HH:MM" start times, which sort correctly as text because they're zero-padded. |
| Filtering | `Scheduler.filter_tasks()`, `Task.is_due()` | Filter by pet name, completion status, or both. Only due tasks are planned, and tasks that don't fit the owner's remaining minutes are skipped with a reason. |
| Conflict handling | `Scheduler.detect_conflicts()`, `Task.fixed_time` | Fixed-time tasks are placed exactly; flexible tasks move past them. Any remaining overlap (e.g. two pets' meds both at 08:00) is reported as a warning in the terminal, in `explain_plan()`, and in the app, instead of crashing. |
| Recurring tasks | `Pet.mark_task_complete()`, `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a task creates a new one due the next day (daily) or 7 days later (weekly), using `date + timedelta`. Calling `Task.mark_complete()` directly only records the date. |

**Tradeoff:** conflict detection only warns. It doesn't move a fixed-time task, because an exact time (like meds) is usually one the owner chose on purpose, so the owner decides how to resolve it.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
