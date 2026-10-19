"""PawPal+ core system: owners, pets, care tasks, and the daily scheduler."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import uuid4

# Text priorities sort alphabetically ("high" < "low" < "medium"), so rank them by number.
PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
FREQUENCIES = ("daily", "weekly")
# How long after completion the next occurrence of a repeating task is due.
REPEAT_INTERVAL = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
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
    fixed_time: Optional[str] = None  # exact "HH:MM" start (e.g. meds); overrides preferred_time
    frequency: str = "daily"  # "daily" or "weekly"
    due_date: Optional[date] = None  # None means due right away
    last_completed: Optional[date] = None  # date this occurrence was done, None if not done yet
    pet_name: str = ""  # set when the task is added to a Pet
    task_id: str = field(default_factory=lambda: uuid4().hex)  # unique even for identical tasks

    def __post_init__(self) -> None:
        """Check the task's values as soon as it is created."""
        self._validate()

    def _validate(self) -> None:
        """Raise ValueError if duration, priority, frequency, or preferred/fixed time is invalid."""
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
        if self.fixed_time is not None:
            try:
                # Store as zero-padded "HH:MM" ("8:00" -> "08:00") so times display consistently.
                self.fixed_time = datetime.strptime(self.fixed_time, "%H:%M").strftime("%H:%M")
            except ValueError:
                raise ValueError(f"fixed_time must be \"HH:MM\", got {self.fixed_time!r}") from None

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

    def is_complete(self) -> bool:
        """Return True if this occurrence of the task has been done."""
        return self.last_completed is not None

    def next_occurrence(self) -> "Task":
        """Return a new, not-yet-done copy of this task due one interval after it was completed."""
        if self.last_completed is None:
            raise ValueError(f"{self.title!r} hasn't been completed yet")
        # Adding a timedelta to a date handles month and year boundaries (Oct 31 + 1 day = Nov 1).
        return replace(
            self,
            due_date=self.last_completed + REPEAT_INTERVAL[self.frequency],
            last_completed=None,
            task_id=uuid4().hex,
        )

    def is_due(self, on: date) -> bool:
        """Return True if the task isn't done yet and its due date has arrived by the given date."""
        if self.is_complete():
            return False
        return self.due_date is None or self.due_date <= on


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

    def mark_task_complete(self, task_id: str, on: Optional[date] = None) -> Task:
        """Complete the task with the given id and add its next occurrence, which is returned."""
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if task is None:
            raise ValueError(f"{self.name} has no task with id {task_id!r}")
        if task.is_complete():
            raise ValueError(f"{task.title!r} is already complete")
        task.mark_complete(on)
        next_task = task.next_occurrence()
        self.add_task(next_task)
        return next_task

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


@dataclass
class ScheduledTask:
    """One task placed in the day's plan, with its start time and why it was chosen."""

    task: Task
    start: datetime
    reason: str

    @property
    def end(self) -> datetime:
        """Return when the task finishes."""
        return self.start + timedelta(minutes=self.task.duration_minutes)

    @property
    def time(self) -> str:
        """Return the start time as zero-padded "HH:MM"."""
        return self.start.strftime("%H:%M")


class Scheduler:
    """Builds one daily care plan across all of an owner's pets, sharing the owner's time."""

    def __init__(self, owner: Owner, day_start: str = "08:00") -> None:
        """Set up a scheduler for the owner, with the day starting at day_start ("HH:MM")."""
        self.owner = owner
        self.day_start = day_start  # "HH:MM" when the first task begins
        self.plan_date: Optional[date] = None
        self.plan: list[ScheduledTask] = []  # in start-time order
        self.skipped: list[tuple[Task, str]] = []  # (task, why it didn't fit)

    def generate_plan(self, on: Optional[date] = None) -> list[ScheduledTask]:
        """Order the due tasks by priority and fit them into the owner's available time."""
        # Start fresh so calling this twice doesn't duplicate tasks.
        self.plan_date = on or date.today()
        self.plan = []
        self.skipped = []

        due = [t for t in self.owner.get_all_tasks() if t.is_due(self.plan_date)]

        # Pick tasks greedily: most important first, shorter first on ties so more fit.
        chosen: list[Task] = []
        remaining = self.owner.available_minutes
        for task in sorted(due, key=lambda t: (-t.priority_rank(), t.duration_minutes)):
            if task.duration_minutes <= remaining:
                chosen.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped.append(
                    (task, f"not enough time left (needs {task.duration_minutes} min, {remaining} min left)")
                )

        # The plan covers one day, so nothing may run past midnight.
        day_end = datetime.combine(self.plan_date + timedelta(days=1), datetime.min.time())

        # Fixed-time tasks go exactly where they were set; everything else works around them.
        for task in chosen:
            if task.fixed_time:
                entry = ScheduledTask(
                    task, self._at(task.fixed_time), f"{task.priority} priority, set for {task.fixed_time}"
                )
                if entry.end > day_end:
                    self.skipped.append((task, f"set for {task.fixed_time}, would run past midnight"))
                else:
                    self.plan.append(entry)
        busy = sorted((s.start, s.end) for s in self.plan)

        # Lay out the other tasks through the day: morning before evening, then by priority.
        flexible = sorted(
            (t for t in chosen if not t.fixed_time),
            key=lambda t: (TIME_OF_DAY_ORDER[t.preferred_time], -t.priority_rank()),
        )
        clock = self._at(self.day_start)
        for task in flexible:
            # Don't start an afternoon or evening task before that part of the day begins.
            if task.preferred_time in TIME_OF_DAY_START:
                clock = max(clock, self._at(TIME_OF_DAY_START[task.preferred_time]))
            start = self._next_free_slot(clock, task.duration_minutes, busy)
            if start + timedelta(minutes=task.duration_minutes) > day_end:
                # Leave the clock where it was so a shorter task later in the list can still fit.
                self.skipped.append((task, "no room left before midnight"))
                continue
            reason = f"{task.priority} priority"
            if task.preferred_time:
                reason += f", preferred in the {task.preferred_time}"
            self.plan.append(ScheduledTask(task, start, reason))
            clock = start + timedelta(minutes=task.duration_minutes)

        self.plan = self.sort_by_time(self.plan)
        return list(self.plan)

    @staticmethod
    def _next_free_slot(
        clock: datetime, minutes: int, busy: list[tuple[datetime, datetime]]
    ) -> datetime:
        """Return the earliest start at or after clock where the task fits between busy times."""
        # busy is sorted by start, so one pass is enough: each jump only moves the clock later.
        for start, end in busy:
            if clock < end and start < clock + timedelta(minutes=minutes):
                clock = end
        return clock

    def find_conflicts(self) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Return each pair of planned tasks whose times overlap (empty if none)."""
        pairs = []
        for i, first in enumerate(self.plan):
            # The plan is sorted by start, so only the tasks that begin before this one ends can overlap it.
            for second in self.plan[i + 1 :]:
                if second.start >= first.end:
                    break
                pairs.append((first, second))
        return pairs

    def detect_conflicts(self) -> list[str]:
        """Return a warning for each pair of planned tasks whose times overlap (empty if none)."""
        return [
            f"{first.task.pet_name}: {first.task.title} ({first.time}-{first.end:%H:%M}) overlaps "
            f"{second.task.pet_name}: {second.task.title} ({second.time}-{second.end:%H:%M})"
            for first, second in self.find_conflicts()
        ]

    def mark_task_complete(self, task_id: str, on: Optional[date] = None) -> Task:
        """Complete a task for whichever pet owns it and return the task's next occurrence."""
        for pet in self.owner.pets:
            if any(t.task_id == task_id for t in pet.tasks):
                return pet.mark_task_complete(task_id, on)
        raise ValueError(f"{self.owner.name}'s pets have no task with id {task_id!r}")

    @staticmethod
    def sort_by_time(entries: list[ScheduledTask]) -> list[ScheduledTask]:
        """Return planned tasks ordered by start time."""
        # Sort by the full date and time, not the "HH:MM" text, which would put
        # a task at 00:30 the next day before one at 23:00.
        return sorted(entries, key=lambda s: s.start)

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> list[Task]:
        """Return the owner's tasks for one pet and/or by completion status (None means any)."""
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.is_complete() == completed]
        return tasks

    def _at(self, hhmm: str) -> datetime:
        """Return the plan date at the given "HH:MM" time."""
        return datetime.combine(self.plan_date, datetime.strptime(hhmm, "%H:%M").time())

    def explain_plan(self) -> str:
        """Explain why each task was scheduled, ordered, or skipped (call generate_plan first)."""
        if self.plan_date is None:
            return "No plan yet. Call generate_plan() first."

        used = sum(s.task.duration_minutes for s in self.plan)
        lines = [
            f"Plan for {self.owner.name} on {self.plan_date:%A, %B %d}: "
            f"{used} of {self.owner.available_minutes} minutes used."
        ]
        if not self.plan:
            lines.append("No tasks scheduled.")
        for s in self.plan:
            lines.append(
                f"  {s.time}  {s.task.pet_name}: {s.task.title} ({s.task.duration_minutes} min) - {s.reason}"
            )
        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("Conflicts:")
            lines.extend(f"  {warning}" for warning in conflicts)
        if self.skipped:
            lines.append("Skipped:")
            for task, reason in self.skipped:
                lines.append(f"  {task.pet_name}: {task.title} - {reason}")
        return "\n".join(lines)
