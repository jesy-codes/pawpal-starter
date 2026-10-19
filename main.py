"""Terminal testing ground: build a small household and print today's schedule."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(scheduler: Scheduler) -> None:
    """Print the scheduler's latest plan as a readable table."""
    owner = scheduler.owner
    used = sum(t.duration_minutes for t in scheduler.scheduled_tasks)

    print("=" * 64)
    print(f"Today's Schedule for {owner.name} - {scheduler.plan_date:%A, %B %d, %Y}")
    print(f"Time used: {used} of {owner.available_minutes} minutes")
    print("=" * 64)
    print(f"{'Time':<7}{'Pet':<8}{'Task':<20}{'Length':<9}Priority")
    print("-" * 64)
    for task in scheduler.scheduled_tasks:
        print(
            f"{scheduler.start_times[task.task_id]:<7}{task.pet_name:<8}{task.title:<20}"
            f"{str(task.duration_minutes) + ' min':<9}{task.priority}"
        )

    if scheduler.skipped_tasks:
        print()
        print("Skipped:")
        for task in scheduler.skipped_tasks:
            print(f"  - {task.pet_name}: {task.title} - {scheduler.reasons[task.task_id]}")

    print()
    print("Why this plan:")
    for task in scheduler.scheduled_tasks:
        print(f"  - {task.title}: {scheduler.reasons[task.task_id]}")


def main() -> None:
    """Create an owner with two pets and their tasks, then print today's plan."""
    owner = Owner("Jordan", available_minutes=90)

    mochi = Pet("Mochi", "dog", breed="Shiba Inu", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Breakfast", 10, "high", category="feeding", preferred_time="morning"))
    mochi.add_task(Task("Evening walk", 30, "high", category="walk", preferred_time="evening"))
    mochi.add_task(Task("Bath and brush", 45, "low", category="grooming", frequency="weekly"))
    luna.add_task(Task("Thyroid medication", 5, "high", category="meds", preferred_time="morning"))
    luna.add_task(Task("Feather toy play", 20, "medium", category="enrichment", preferred_time="afternoon"))
    luna.add_task(Task("Brush coat", 10, "medium", category="grooming"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan(date.today())
    print_schedule(scheduler)


if __name__ == "__main__":
    main()
