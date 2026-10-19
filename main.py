"""Terminal testing ground: build a small household and print today's schedule."""

from datetime import date

from pawpal_system import Owner, Pet, ScheduledTask, Scheduler, Task


def print_schedule(scheduler: Scheduler) -> None:
    """Print the scheduler's latest plan as a readable table."""
    owner = scheduler.owner
    used = sum(s.task.duration_minutes for s in scheduler.plan)

    print("=" * 64)
    print(f"Today's Schedule for {owner.name} - {scheduler.plan_date:%A, %B %d, %Y}")
    print(f"Time used: {used} of {owner.available_minutes} minutes")
    print("=" * 64)
    print(f"{'Time':<7}{'Pet':<8}{'Task':<20}{'Length':<9}Priority")
    print("-" * 64)
    for s in scheduler.plan:
        print(
            f"{s.time:<7}{s.task.pet_name:<8}{s.task.title:<20}"
            f"{str(s.task.duration_minutes) + ' min':<9}{s.task.priority}"
        )

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print()
        print("Conflicts:")
        for warning in conflicts:
            print(f"  ! {warning}")

    if scheduler.skipped:
        print()
        print("Skipped:")
        for task, reason in scheduler.skipped:
            print(f"  - {task.pet_name}: {task.title} - {reason}")

    print()
    print("Why this plan:")
    for s in scheduler.plan:
        print(f"  - {s.task.title}: {s.reason}")


def print_plan(heading: str, entries: list[ScheduledTask]) -> None:
    """Print a heading and one line per planned task with its start time."""
    print(heading)
    for s in entries:
        print(f"  {s.time}  {s.task.pet_name:<7}{s.task.title}")
    print()


def print_tasks(heading: str, tasks: list[Task]) -> None:
    """Print a heading and one line per task with whether it's done or when it's due."""
    print(heading)
    if not tasks:
        print("  (none)")
    for task in tasks:
        if task.is_complete():
            status = f"done {task.last_completed:%b %d}"
        else:
            status = f"due {task.due_date:%b %d}" if task.due_date else "due now"
        print(f"  {task.pet_name:<7}{task.title:<20}{status}")
    print()


def main() -> None:
    """Create an owner with two pets and their tasks, then print today's plan."""
    owner = Owner("Jordan", available_minutes=90)

    mochi = Pet("Mochi", "dog", breed="Shiba Inu", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of order on purpose: evening and afternoon tasks before morning ones.
    mochi.add_task(Task("Evening walk", 30, "high", category="walk", preferred_time="evening"))
    luna.add_task(Task("Feather toy play", 20, "medium", category="enrichment", preferred_time="afternoon"))
    mochi.add_task(Task("Bath and brush", 45, "low", category="grooming", frequency="weekly"))
    luna.add_task(Task("Brush coat", 10, "medium", category="grooming"))
    luna.add_task(Task("Thyroid medication", 5, "high", category="meds", fixed_time="08:00"))
    # Set for the same time as Luna's meds, so the scheduler reports a conflict.
    mochi.add_task(Task("Joint supplement", 5, "high", category="meds", fixed_time="08:00"))
    mochi.add_task(Task("Breakfast", 10, "high", category="feeding", preferred_time="morning"))

    # Luna was already brushed today: the next brushing is created for tomorrow.
    next_brush = luna.mark_task_complete(luna.tasks[1].task_id, date.today())
    print(f"Completed {next_brush.title!r} for {next_brush.pet_name}; next one due {next_brush.due_date:%A, %B %d}")
    print()

    scheduler = Scheduler(owner)
    scheduler.generate_plan(date.today())
    print_schedule(scheduler)

    print()
    shuffled = scheduler.plan[::-1]
    print_plan("Plan, out of order:", shuffled)
    print_plan("Plan, sorted by start time:", scheduler.sort_by_time(shuffled))
    print_tasks("Luna's tasks:", scheduler.filter_tasks(pet_name="Luna"))
    print_tasks("Completed tasks:", scheduler.filter_tasks(completed=True))
    print_tasks("Mochi's tasks still to do:", scheduler.filter_tasks(pet_name="Mochi", completed=False))


if __name__ == "__main__":
    main()
