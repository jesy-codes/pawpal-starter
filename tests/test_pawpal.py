from datetime import date

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


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
