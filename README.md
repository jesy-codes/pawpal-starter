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

## ✨ Features

- **Multi-pet planning with a shared time budget:** one owner, any number of pets. The scheduler gathers every pet's tasks through `Owner.get_all_tasks()`, so all pets share the owner's available minutes instead of each getting the full day.
- **Priority-first task selection:** due tasks are chosen high → medium → low (shorter first on ties so more fit) until the owner's time runs out. Priorities are ranked by number, not sorted as text, so "low" never comes before "medium".
- **Skipped tasks with reasons:** anything that doesn't fit lands in a "didn't fit" list with the exact reason, e.g. "not enough time left (needs 45 min, 20 min left)".
- **Time-of-day placement:** tasks can prefer morning, afternoon, or evening. Afternoon tasks start no earlier than 12:00 and evening tasks no earlier than 18:00; tasks with no preference fill in after the morning ones.
- **Fixed-time tasks:** a task can be pinned to an exact "HH:MM" (like meds at 08:00). Fixed tasks are placed first, and flexible tasks are moved to the next free slot around them.
- **Sorting by time:** the plan is always shown in start-time order. `sort_by_time()` sorts by the full date and time, so it stays correct even across midnight.
- **Conflict warnings:** `find_conflicts()` / `detect_conflicts()` flag any two planned tasks whose time ranges overlap (not just identical start times), naming both pets, tasks, and times. Back-to-back tasks are not flagged.
- **Daily and weekly recurrence:** marking a task complete records the date and creates its next occurrence, due the next day (daily) or 7 days later (weekly), across month and year boundaries. Completed tasks drop out of today's plan.
- **Filtering:** view tasks for one pet, by status (to do / done), or both, with `filter_tasks()`.
- **Day boundary:** nothing is scheduled to run past midnight; such tasks are skipped with a reason.
- **Input validation:** invalid priorities, frequencies, durations, or times like "25:00" are rejected with a clear message, and duplicate pet names are blocked.
- **Plan explanation:** every scheduled task carries a reason ("high priority, preferred in the evening", "set for 08:00"), and `explain_plan()` summarizes the whole day.

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

The core logic lives in `pawpal_system.py` (diagram: `diagrams/uml_final.mmd`) and is built from five classes:

- **Task** (dataclass): one care activity with a duration, a priority (high/medium/low), an optional time of day (morning/afternoon/evening), an optional exact `fixed_time` ("HH:MM", e.g. for meds), and a frequency (daily/weekly). Completing a task through `Pet.mark_task_complete()` (or `Scheduler.mark_task_complete()`) records the date and adds a new occurrence due the next day (daily) or 7 days later (weekly); `is_due()` skips finished tasks and ones whose due date hasn't arrived. Each task gets a unique id and is checked for invalid values when created or edited.
- **Pet** (dataclass): a pet's details and its list of tasks. `add_task()` links each task to the pet by name, `remove_task()` removes by id, and `mark_task_complete()` completes a task and adds its next occurrence.
- **Owner** (dataclass): the owner's name, the minutes they have available today, and their pets. `get_all_tasks()` returns every pet's tasks in one list.
- **ScheduledTask** (dataclass): one entry in the day's plan, holding the `task`, its `start` time, and the `reason` it was chosen, with `end` and `time` ("HH:MM") worked out from them.
- **Scheduler**: builds one daily plan for the owner as a list of `ScheduledTask`s (`plan`, in start-time order) plus `skipped`, a list of `(task, reason)` pairs. `generate_plan()` reads `owner.get_all_tasks()`, keeps the tasks that are due, and picks them by priority until the owner's time runs out; tasks that don't fit are skipped with a reason. It then gives each chosen task a start time: fixed-time tasks go exactly at their set time, and the rest are laid out from 08:00 (afternoon tasks at 12:00 or later, evening tasks at 18:00 or later), moving past any fixed-time task they would overlap. `sort_by_time()` orders planned tasks by start time, `filter_tasks()` filters by pet and/or completion status, `find_conflicts()` returns overlapping pairs and `detect_conflicts()` turns them into warnings, and `explain_plan()` describes why each task was scheduled, skipped, or in conflict.

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

Run the full test suite from the project folder:

```bash
python -m pytest
```

The 21 tests in `tests/test_pawpal.py` cover:

- **Tasks and pets:** marking a task complete, adding tasks to a pet, and rejecting an invalid fixed time.
- **Sorting:** the plan comes out in clock order (including with a fixed-time task in the middle), and `sort_by_time()` uses the full date, so a task after midnight sorts after one late in the evening.
- **Choosing what fits:** higher priority wins when time is short, a task that exactly fills the remaining time still fits, an owner whose pet has no tasks gets an empty plan, and generating twice doesn't duplicate tasks.
- **Recurrence:** completing a daily or weekly task creates its next occurrence (across month and year boundaries), a completed task leaves today's plan and returns tomorrow, a missed occurrence stays due, and completing the same task twice is rejected.
- **Conflicts and time slots:** overlapping tasks are flagged (including two pets at the exact same time), `find_conflicts()` returns exactly the overlapping pair, back-to-back tasks are not, flexible tasks move around fixed ones, and tasks that would run past midnight are skipped.
- **Filtering:** by pet, by completion status, and both together.

Output of a successful run:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/jmrt/Documents/jesy-codes/code_path/pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 21 items

tests/test_pawpal.py .....................                               [100%]

============================== 21 passed in 0.11s ==============================
```

**Confidence Level: ⭐⭐⭐⭐☆ (4/5)**

All 21 tests pass, and they cover the scheduler's core rules plus the edge cases most likely to break it (exact fits, back-to-back times, midnight, month and year rollovers). Testing also caught a real bug: plans that ran past midnight were sorted in the wrong order. I'm not at 5 stars because the Streamlit UI in `app.py` has no automated tests, and the greedy pick-by-priority approach can leave time unused in some cases (a known tradeoff, not a crash).

## 📐 Smarter Scheduling

All of these live in `pawpal_system.py`.

| Feature | Method(s) |
|---------|-----------|
| Sorting | `Scheduler.sort_by_time()`, `Scheduler.generate_plan()` |
| Filtering | `Scheduler.filter_tasks()`, `Task.is_due()` |
| Conflict detection | `Scheduler.find_conflicts()`, `Scheduler.detect_conflicts()`, `Scheduler._next_free_slot()` |
| Recurring tasks | `Pet.mark_task_complete()`, `Scheduler.mark_task_complete()`, `Task.next_occurrence()` |

### Sorting
- **`Scheduler.sort_by_time(entries)`** returns planned tasks (`ScheduledTask`s) in start-time order using `sorted(entries, key=lambda s: s.start)`. It sorts by the full date and time rather than the "HH:MM" text, which would put a task at 00:30 the next day before one at 23:00.
- **`Scheduler.generate_plan()`** picks tasks by priority (high → medium → low), shorter first on ties so more fit. It then sorts the finished plan with `sort_by_time()`.

### Filtering
- **`Scheduler.filter_tasks(pet_name=None, completed=None)`** returns the owner's tasks for one pet, by completion status, or both. Leaving an argument as `None` means "don't filter on this". Example: `filter_tasks(pet_name="Mochi", completed=False)` gives Mochi's tasks still to do.
- **`Task.is_due(on)`** keeps finished tasks and tasks due on a later date out of the plan.

### Conflict detection
- **`Scheduler.detect_conflicts()`** returns a warning for each pair of planned tasks whose time ranges overlap, not just ones with the same start time. Because the plan is sorted, it compares each task only with the tasks that start before it ends. Example warning: `Mochi: Joint supplement (08:00-08:05) overlaps Luna: Thyroid medication (08:00-08:05)`.
- **`Scheduler._next_free_slot()`** prevents most conflicts in the first place. Tasks with a `fixed_time` (like meds at 08:00) are placed first, and flexible tasks move past them. So only two fixed-time tasks can still overlap.
- Nothing may run past midnight: a task that would is skipped with a reason ("would run past midnight" or "no room left before midnight").
- Conflicts are warnings, not errors. They show up in `main.py`, in `explain_plan()`, and in the app, and the scheduler doesn't move fixed-time tasks on its own.

### Recurring tasks
- **`Pet.mark_task_complete(task_id, on)`** marks a task done and adds its next occurrence. **`Scheduler.mark_task_complete()`** does the same when you only have the task id and not the pet.
- **`Task.next_occurrence()`** creates the new task due `last_completed + timedelta(days=1)` for daily tasks or `+ timedelta(weeks=1)` for weekly ones. `timedelta` handles month and year rollovers (Oct 31 → Nov 1, Dec 28 → Jan 4).
- Calling `Task.mark_complete()` directly only records the date and doesn't create the next occurrence.

## 📸 Demo Walkthrough

Start the app with `streamlit run app.py`. Everything you enter is kept in `st.session_state` while the app is open.

### Main UI features

| Section | What you can do |
|---|---|
| **Owner** | Set your name and how many minutes you have available today. |
| **Pets** | Add a pet (name, species, optional breed, age). Pets appear in a table with their task count; duplicate names are rejected. |
| **Tasks** | Add a task for a chosen pet: title, category, duration, priority, time of day (any/morning/afternoon/evening), an optional exact time ("HH:MM"), and whether it repeats daily or weekly. |
| **Task list** | Filter by pet and by status (All / To do / Done). Each row shows when the task is due and whether it's done. |
| **Mark a task done** | Pick a task and click **Mark complete**. The app confirms it and says when the next occurrence is due. |
| **Today's Schedule** | Click **Generate schedule** to see a summary (tasks scheduled, time used, conflicts), the plan sorted by start time with a reason for each task, conflict and "didn't fit" warnings, and a full written explanation. The plan updates as you add or complete tasks. |

### Example workflow

1. **Set up the owner.** Enter "Jordan" and 90 minutes available.
2. **Add two pets.** Add Mochi (dog) and Luna (cat). Both appear in the Pets table.
3. **Add tasks.**
   - Mochi: "Joint supplement", 5 min, high, exact time 08:00
   - Luna: "Thyroid medication", 5 min, high, exact time 08:00
   - Mochi: "Breakfast", 10 min, high, morning
   - Luna: "Feather toy play", 20 min, medium, afternoon
   - Mochi: "Evening walk", 30 min, high, evening
   - Mochi: "Bath and brush", 45 min, low, weekly
4. **Generate the schedule.** Click **Generate schedule**. The summary shows 5 tasks, 70 / 90 min, and 1 conflict.
5. **Read the warnings.** A red box explains that Mochi's Joint supplement (08:00-08:05) overlaps Luna's Thyroid medication (08:00-08:05) and suggests changing one task's exact time or clearing it so PawPal+ can find a free slot. Both rows are marked "⚠️ conflict" in the table. A yellow box lists Bath and brush under "Didn't fit today" with the reason.
6. **Complete a task.** Mark Mochi's Breakfast done. The app says the next one is due tomorrow; the task list shows today's Breakfast as "✅ Done" and a new Breakfast due tomorrow, and Breakfast leaves today's plan.
7. **Filter.** Choose "Luna" and "To do" to see only Luna's remaining tasks.

### Key Scheduler behaviors shown

- **Sorting:** tasks entered in any order appear in start-time order (08:00 → 12:00 → 18:00).
- **Priority selection and skipping:** high-priority tasks are chosen first; the 45-minute low-priority bath doesn't fit and is listed with its reason.
- **Time-of-day placement:** afternoon play starts at 12:00 and the evening walk at 18:00, not right after breakfast.
- **Fixed times and conflict warnings:** the two 08:00 meds stay at 08:00 and are flagged as a conflict, while Breakfast is moved to 08:05 so it doesn't overlap them.
- **Recurrence:** completing a daily task creates tomorrow's occurrence automatically.
- **Filtering:** the task list narrows by pet and by completion status.

### Sample CLI output (`python main.py`)

`main.py` runs the same kind of scenario in the terminal. It completes Luna's "Brush coat" first, prints today's schedule, then shows the plan before and after sorting and the filtered task lists:

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

Plan, out of order:
  18:00  Mochi  Evening walk
  12:00  Luna   Feather toy play
  08:05  Mochi  Breakfast
  08:00  Luna   Thyroid medication
  08:00  Mochi  Joint supplement

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

Mochi's tasks still to do:
  Mochi  Evening walk        due now
  Mochi  Bath and brush      due now
  Mochi  Joint supplement    due now
  Mochi  Breakfast           due now
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
