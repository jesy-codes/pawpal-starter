"""PawPal+ core system: owners, pets, care tasks, and the daily scheduler."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import uuid4

# Text priorities sort alphabetically ("high" < "low" < "medium"), so rank them by number.
PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
FREQUENCIES = ("daily", "weekly")
# Order of the day; tasks with no preferred time fill in right after the morning ones.
TIME_OF_DAY_ORDER = {"morning": 0, None: 1, "afternoon": 2, "evening": 3}
# Earliest start for later parts of the day (morning starts at the scheduler's day_start).
TIME_OF_DAY_START = {"afternoon": "12:00", "evening": "18:00"}


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, grooming, enrichment)."""

    title: str
    duration_minutes: int
    priority: str  # "high", "medium", or "low"
    category: str = "general"
    preferred_time: Optional[str] = None  # "morning", "afternoon", or "evening"
    frequency: str = "daily"  # "daily" or "weekly"
    last_completed: Optional[date] = None  # completion is tracked by date so it resets
    pet_name: str = ""  # set when the task is added to a Pet
    task_id: str = field(default_factory=lambda: uuid4().hex)  # unique even for identical tasks

    def __post_init__(self) -> None:
        """Check the task's values as soon as it is created."""
        self._validate()

    def _validate(self) -> None:
        """Raise ValueError if duration, priority, frequency, or preferred time is invalid."""
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}, got {self.frequency!r}")
        if self.preferred_time not in TIME_OF_DAY_ORDER:
            raise ValueError(
                f"preferred_time must be morning, afternoon, evening, or None, got {self.preferred_time!r}"
            )

    def priority_rank(self) -> int:
        """Return the numeric rank of this task's priority (higher is more important)."""
        return PRIORITY_RANK[self.priority]

    def edit(self, title: str, duration_minutes: int, priority: str) -> None:
        """Update the task's title, duration, and priority."""
        old = (self.title, self.duration_minutes, self.priority)
        self.title, self.duration_minutes, self.priority = title, duration_minutes, priority
        try:
            self._validate()
        except ValueError:
            # Leave the task unchanged if the new values are invalid.
            self.title, self.duration_minutes, self.priority = old
            raise

    def mark_complete(self, on: Optional[date] = None) -> None:
        """Record that this task was done on the given date (today by default)."""
        self.last_completed = on or date.today()

    def is_due(self, on: date) -> bool:
        """Return True if the task still needs doing on the given date, based on its frequency."""
        if self.last_completed is None:
            return True
        days_since = (on - self.last_completed).days
        if self.frequency == "daily":
            return days_since >= 1
        return days_since >= 7


@dataclass
class Pet:
    """The animal being cared for, along with its care tasks."""

    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and link the task to this pet by name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the care task with the given id from this pet."""
        remaining = [t for t in self.tasks if t.task_id != task_id]
        if len(remaining) == len(self.tasks):
            raise ValueError(f"{self.name} has no task with id {task_id!r}")
        self.tasks = remaining

    def get_tasks(self) -> list[Task]:
        """Return all care tasks for this pet."""
        return list(self.tasks)


@dataclass
class Owner:
    """The person responsible for the pet's care and the day's constraints."""

    name: str
    available_minutes: int = 0
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        # Tasks point back to their pet by name, so names must be unique.
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def set_available_time(self, minutes: int) -> None:
        """Set how many minutes the owner has available today."""
        if minutes < 0:
            raise ValueError(f"available minutes can't be negative, got {minutes}")
        self.available_minutes = minutes

    def get_all_tasks(self) -> list[Task]:
        """Return the tasks of every pet this owner has."""
        return [task for pet in self.pets for task in pet.get_tasks()]


class Scheduler:
    """Builds one daily care plan across all of an owner's pets, sharing the owner's time."""

    def __init__(self, owner: Owner, day_start: str = "08:00") -> None:
        """Set up a scheduler for the owner, with the day starting at day_start ("HH:MM")."""
        self.owner = owner
        self.day_start = day_start  # "HH:MM" when the first task begins
        self.plan_date: Optional[date] = None
        self.scheduled_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []
        self.start_times: dict[str, str] = {}  # task_id -> "HH:MM"
        self.reasons: dict[str, str] = {}  # task_id -> why it was scheduled or skipped

    def generate_plan(self, on: Optional[date] = None) -> list[Task]:
        """Order the due tasks by priority and fit them into the owner's available time."""
        # Start fresh so calling this twice doesn't duplicate tasks.
        self.plan_date = on or date.today()
        self.scheduled_tasks = []
        self.skipped_tasks = []
        self.start_times = {}
        self.reasons = {}

        due = [t for t in self.owner.get_all_tasks() if t.is_due(self.plan_date)]

        # Pick tasks greedily: most important first, shorter first on ties so more fit.
        remaining = self.owner.available_minutes
        for task in sorted(due, key=lambda t: (-t.priority_rank(), t.duration_minutes)):
            if task.duration_minutes <= remaining:
                self.scheduled_tasks.append(task)
                remaining -= task.duration_minutes
                self.reasons[task.task_id] = f"{task.priority} priority"
            else:
                self.skipped_tasks.append(task)
                self.reasons[task.task_id] = (
                    f"not enough time left (needs {task.duration_minutes} min, {remaining} min left)"
                )

        # Lay out the chosen tasks through the day: morning before evening, then by priority.
        self.scheduled_tasks.sort(
            key=lambda t: (TIME_OF_DAY_ORDER[t.preferred_time], -t.priority_rank())
        )
        clock = self._at(self.day_start)
        for task in self.scheduled_tasks:
            # Don't start an afternoon or evening task before that part of the day begins.
            if task.preferred_time in TIME_OF_DAY_START:
                clock = max(clock, self._at(TIME_OF_DAY_START[task.preferred_time]))
            self.start_times[task.task_id] = clock.strftime("%H:%M")
            if task.preferred_time:
                self.reasons[task.task_id] += f", preferred in the {task.preferred_time}"
            clock += timedelta(minutes=task.duration_minutes)

        return list(self.scheduled_tasks)

    def _at(self, hhmm: str) -> datetime:
        """Return the plan date at the given "HH:MM" time."""
        return datetime.combine(self.plan_date, datetime.strptime(hhmm, "%H:%M").time())

    def explain_plan(self) -> str:
        """Explain why each task was scheduled, ordered, or skipped (call generate_plan first)."""
        if self.plan_date is None:
            return "No plan yet. Call generate_plan() first."

        used = sum(t.duration_minutes for t in self.scheduled_tasks)
        lines = [
            f"Plan for {self.owner.name} on {self.plan_date:%A, %B %d}: "
            f"{used} of {self.owner.available_minutes} minutes used."
        ]
        if not self.scheduled_tasks:
            lines.append("No tasks scheduled.")
        for task in self.scheduled_tasks:
            lines.append(
                f"  {self.start_times[task.task_id]}  {task.pet_name}: {task.title} "
                f"({task.duration_minutes} min) - {self.reasons[task.task_id]}"
            )
        if self.skipped_tasks:
            lines.append("Skipped:")
            for task in self.skipped_tasks:
                lines.append(f"  {task.pet_name}: {task.title} - {self.reasons[task.task_id]}")
        return "\n".join(lines)
