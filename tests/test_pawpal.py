from datetime import date, datetime

import pytest

from pawpal_system import Owner, Pet, ScheduledTask, Scheduler, Task


def test_mark_complete_changes_task_status():
    task = Task("Breakfast", 10, "high")
    today = date(2026, 10, 18)
    assert task.last_completed is None
    assert task.is_due(today)

    task.mark_complete(today)

    assert task.last_completed == today
    assert not task.is_due(today)


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Evening walk", 30, "high"))

    assert len(pet.get_tasks()) == 1


def test_sort_by_time_orders_tasks_by_start_time():
    owner = Owner("Jordan", available_minutes=60)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    walk = Task("Evening walk", 30, "high", preferred_time="evening")
    breakfast = Task("Breakfast", 10, "high", preferred_time="morning")
    play = Task("Play", 15, "low", preferred_time="afternoon")
    for task in (walk, play, breakfast):
        pet.add_task(task)
    scheduler = Scheduler(owner)
    scheduler.generate_plan(date(2026, 10, 18))

    out_of_order = scheduler.plan[::-1]

    assert [s.task for s in scheduler.sort_by_time(out_of_order)] == [breakfast, play, walk]


def test_filter_tasks_by_pet_and_completion():
    owner = Owner("Jordan", available_minutes=60)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    walk = Task("Walk", 30, "high")
    brush = Task("Brush", 10, "medium")
    meds = Task("Meds", 5, "high")
    mochi.add_task(walk)
    luna.add_task(brush)
    luna.add_task(meds)
    today = date(2026, 10, 18)
    brush.mark_complete(today)
    scheduler = Scheduler(owner)
    scheduler.generate_plan(today)

    assert scheduler.filter_tasks(pet_name="Luna") == [brush, meds]
    assert scheduler.filter_tasks(completed=True) == [brush]
    assert scheduler.filter_tasks(pet_name="Luna", completed=False) == [meds]


def test_completing_daily_task_creates_one_for_tomorrow():
    pet = Pet("Mochi", "dog")
    breakfast = Task("Breakfast", 10, "high")
    pet.add_task(breakfast)

    next_task = pet.mark_task_complete(breakfast.task_id, date(2026, 10, 31))

    assert breakfast.is_complete()
    assert next_task.due_date == date(2026, 11, 1)
    assert not next_task.is_complete()
    assert next_task.task_id != breakfast.task_id
    assert pet.get_tasks() == [breakfast, next_task]
    assert not next_task.is_due(date(2026, 10, 31))
    assert next_task.is_due(date(2026, 11, 1))


def test_completing_weekly_task_creates_one_a_week_later():
    owner = Owner("Jordan", available_minutes=60)
    pet = Pet("Luna", "cat")
    owner.add_pet(pet)
    bath = Task("Bath", 30, "low", frequency="weekly")
    pet.add_task(bath)

    next_task = Scheduler(owner).mark_task_complete(bath.task_id, date(2026, 12, 28))

    assert next_task.due_date == date(2027, 1, 4)
    assert next_task.frequency == "weekly"
    assert next_task.pet_name == "Luna"


def _owner_with(*tasks):
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    for task in tasks:
        pet.add_task(task)
    return owner


def test_tasks_at_the_same_fixed_time_are_reported_as_conflicts():
    meds = Task("Meds", 10, "high", fixed_time="8:00")
    vitamins = Task("Vitamins", 5, "high", fixed_time="08:05")
    scheduler = Scheduler(_owner_with(meds, vitamins))
    scheduler.generate_plan(date(2026, 10, 18))

    conflicts = scheduler.detect_conflicts()

    assert meds.fixed_time == "08:00"
    assert len(conflicts) == 1
    assert "Meds (08:00-08:10) overlaps Mochi: Vitamins (08:05-08:10)" in conflicts[0]


def test_flexible_tasks_are_placed_around_fixed_ones():
    meds = Task("Meds", 10, "high", fixed_time="08:10")
    breakfast = Task("Breakfast", 15, "high", preferred_time="morning")
    scheduler = Scheduler(_owner_with(meds, breakfast))
    scheduler.generate_plan(date(2026, 10, 18))

    # Breakfast won't fit in the 10 minutes before the meds, so it moves to after them.
    assert [(s.task, s.time) for s in scheduler.plan] == [(meds, "08:10"), (breakfast, "08:20")]
    assert scheduler.detect_conflicts() == []


def test_invalid_fixed_time_is_rejected():
    with pytest.raises(ValueError):
        Task("Meds", 10, "high", fixed_time="25:00")


# --- Edge cases -----------------------------------------------------------------------


def test_owner_with_a_pet_but_no_tasks_gets_an_empty_plan():
    owner = Owner("Jordan", available_minutes=60)
    owner.add_pet(Pet("Mochi", "dog"))
    scheduler = Scheduler(owner)

    assert scheduler.generate_plan(date(2026, 10, 18)) == []
    assert scheduler.skipped == []
    assert scheduler.detect_conflicts() == []
    assert "No tasks scheduled." in scheduler.explain_plan()


def test_generated_plan_is_in_chronological_order():
    walk = Task("Evening walk", 30, "high", preferred_time="evening")
    meds = Task("Meds", 5, "high", fixed_time="13:00")
    breakfast = Task("Breakfast", 10, "low", preferred_time="morning")
    scheduler = Scheduler(_owner_with(walk, meds, breakfast))

    plan = scheduler.generate_plan(date(2026, 10, 18))

    assert [s.task for s in plan] == [breakfast, meds, walk]
    assert [s.start for s in plan] == sorted(s.start for s in plan)


def test_higher_priority_wins_when_time_is_short():
    owner = Owner("Jordan", available_minutes=30)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    walk = Task("Walk", 30, "high")  # exactly fills the available time
    play = Task("Play", 10, "low")
    pet.add_task(play)
    pet.add_task(walk)
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(date(2026, 10, 18))

    assert [s.task for s in plan] == [walk]
    assert [task for task, _ in scheduler.skipped] == [play]


def test_completed_task_leaves_todays_plan_and_returns_tomorrow():
    breakfast = Task("Breakfast", 10, "high")
    owner = _owner_with(breakfast)
    scheduler = Scheduler(owner)
    today, tomorrow = date(2026, 10, 18), date(2026, 10, 19)

    next_task = scheduler.mark_task_complete(breakfast.task_id, today)

    assert scheduler.generate_plan(today) == []
    assert [s.task for s in scheduler.generate_plan(tomorrow)] == [next_task]


def test_missed_recurring_task_is_still_due_later():
    pet = Pet("Mochi", "dog")
    breakfast = Task("Breakfast", 10, "high")
    pet.add_task(breakfast)

    next_task = pet.mark_task_complete(breakfast.task_id, date(2026, 10, 18))

    # Due Oct 19 but not done, so it should still show up on Oct 21.
    assert next_task.is_due(date(2026, 10, 21))


def test_completing_a_task_twice_is_rejected():
    pet = Pet("Mochi", "dog")
    breakfast = Task("Breakfast", 10, "high")
    pet.add_task(breakfast)
    pet.mark_task_complete(breakfast.task_id, date(2026, 10, 18))

    with pytest.raises(ValueError):
        pet.mark_task_complete(breakfast.task_id, date(2026, 10, 18))
    assert len(pet.get_tasks()) == 2  # no extra occurrence was added


def test_two_pets_with_tasks_at_the_exact_same_time_conflict():
    owner = Owner("Jordan", available_minutes=60)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Meds", 5, "high", fixed_time="08:00"))
    luna.add_task(Task("Meds", 5, "high", fixed_time="08:00"))
    scheduler = Scheduler(owner)
    scheduler.generate_plan(date(2026, 10, 18))

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "Mochi: Meds" in conflicts[0] and "Luna: Meds" in conflicts[0]


def test_back_to_back_fixed_tasks_do_not_conflict():
    meds = Task("Meds", 10, "high", fixed_time="08:00")
    walk = Task("Walk", 20, "high", fixed_time="08:10")  # starts the minute meds end
    scheduler = Scheduler(_owner_with(meds, walk))
    scheduler.generate_plan(date(2026, 10, 18))

    assert scheduler.detect_conflicts() == []


def test_generating_twice_does_not_duplicate_tasks():
    scheduler = Scheduler(_owner_with(Task("Walk", 20, "high"), Task("Play", 200, "low")))

    scheduler.generate_plan(date(2026, 10, 18))
    scheduler.generate_plan(date(2026, 10, 18))

    assert len(scheduler.plan) == 1
    assert len(scheduler.skipped) == 1


def test_sort_by_time_uses_the_date_not_just_the_clock_time():
    task_a, task_b = Task("A", 10, "high"), Task("B", 10, "high")
    late_tonight = ScheduledTask(task_a, datetime(2026, 10, 18, 23, 0), "")
    after_midnight = ScheduledTask(task_b, datetime(2026, 10, 19, 0, 30), "")

    # As "HH:MM" text, "00:30" would sort before "23:00".
    assert Scheduler.sort_by_time([after_midnight, late_tonight]) == [late_tonight, after_midnight]


def test_tasks_that_would_run_past_midnight_are_skipped():
    owner = Owner("Jordan", available_minutes=600)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    evening = [Task(f"Evening task {i}", 120, "high", preferred_time="evening") for i in range(4)]
    late_meds = Task("Late meds", 30, "high", fixed_time="23:45")
    short = Task("Short task", 10, "low", preferred_time="evening")
    for task in (*evening, late_meds, short):
        pet.add_task(task)
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(date(2026, 10, 18))

    # 18:00-20:00, 20:00-22:00, 22:00-00:00 fit (ending exactly at midnight is fine); the 4th doesn't.
    assert [s.time for s in plan] == ["18:00", "20:00", "22:00"]
    assert all(s.end <= datetime(2026, 10, 19) for s in plan)
    skipped = {task.title: reason for task, reason in scheduler.skipped}
    assert skipped["Late meds"] == "set for 23:45, would run past midnight"
    assert skipped["Evening task 3"] == "no room left before midnight"
    assert skipped["Short task"] == "no room left before midnight"


def test_find_conflicts_returns_the_overlapping_pair():
    meds = Task("Meds", 10, "high", fixed_time="08:00")
    vitamins = Task("Vitamins", 5, "high", fixed_time="08:05")
    walk = Task("Walk", 20, "high", fixed_time="09:00")
    scheduler = Scheduler(_owner_with(meds, vitamins, walk))
    scheduler.generate_plan(date(2026, 10, 18))

    pairs = scheduler.find_conflicts()

    assert [(first.task, second.task) for first, second in pairs] == [(meds, vitamins)]
