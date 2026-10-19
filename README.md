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

The core logic lives in `pawpal_system.py` (diagram: `diagrams/uml.mmd`) and is built from four classes:

- **Task** (dataclass): one care activity with a duration, a priority (high/medium/low), an optional time of day (morning/afternoon/evening), and a frequency (daily/weekly). Completion is stored as a date, so `is_due()` brings a daily task back the next day and a weekly task back after 7 days. Each task gets a unique id and is checked for invalid values when created or edited.
- **Pet** (dataclass): a pet's details and its list of tasks. `add_task()` links each task to the pet by name, and `remove_task()` removes by id.
- **Owner** (dataclass): the owner's name, the minutes they have available today, and their pets. `get_all_tasks()` returns every pet's tasks in one list.
- **Scheduler**: builds one daily plan for the owner. `generate_plan()` reads `owner.get_all_tasks()`, keeps the tasks that are due, and picks them by priority until the owner's time runs out; tasks that don't fit are skipped with a reason. It then orders the chosen tasks through the day and gives each a start time (from 08:00; afternoon tasks start at 12:00 or later and evening tasks at 18:00 or later). `explain_plan()` describes why each task was scheduled or skipped.

How they work together: an **Owner** has **Pets**, each **Pet** has **Tasks**, and the **Scheduler** asks the Owner for all tasks so every pet shares the same time budget.

`main.py` builds a sample owner with two pets and prints today's schedule; `tests/test_pawpal.py` holds the tests.

## 🖥️ Sample Output

Output of `python main.py` (one owner, two pets, 90 minutes available):

```
================================================================
Today's Schedule for Jordan - Sunday, October 18, 2026
Time used: 75 of 90 minutes
================================================================
Time   Pet     Task                Length   Priority
----------------------------------------------------------------
08:00  Luna    Thyroid medication  5 min    high
08:05  Mochi   Breakfast           10 min   high
08:15  Luna    Brush coat          10 min   medium
12:00  Luna    Feather toy play    20 min   medium
18:00  Mochi   Evening walk        30 min   high

Skipped:
  - Mochi: Bath and brush - not enough time left (needs 45 min, 15 min left)

Why this plan:
  - Thyroid medication: high priority, preferred in the morning
  - Breakfast: high priority, preferred in the morning
  - Brush coat: medium priority
  - Feather toy play: medium priority, preferred in the afternoon
  - Evening walk: high priority, preferred in the evening
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
