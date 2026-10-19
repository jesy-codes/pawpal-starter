"""PawPal+ core system: class skeletons based on diagrams/uml.mmd."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import uuid4

# Text priorities sort alphabetically ("high" < "low" < "medium"), so rank them by number.
PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
FREQUENCIES = ("daily", "weekly")


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, grooming, enrichment)."""

    title: str
    duration_minutes: int
    priority: str  # "high", "medium", or "low"
    category: str = "general"
    preferred_time: Optional[str] = None  # e.g. "morning", "evening"
    frequency: str = "daily"  # "daily" or "weekly"
    last_completed: Optional[date] = None  # completion is tracked by date so it resets
    pet_name: str = ""  # set when the task is added to a Pet
    task_id: str = field(default_factory=lambda: uuid4().hex)  # unique even for identical tasks

    def __post_init__(self) -> None:
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}, got {self.frequency!r}")

    def priority_rank(self) -> int:
        """Return the numeric rank of this task's priority (higher is more important)."""
        return PRIORITY_RANK[self.priority]

    def edit(self, title: str, duration_minutes: int, priority: str) -> None:
        """Update the task's title, duration, and priority."""
        pass

    def mark_complete(self, on: Optional[date] = None) -> None:
        """Record that this task was done on the given date (today by default)."""
        pass

    def is_due(self, on: date) -> bool:
        """Return True if the task still needs doing on the given date, based on its frequency."""
        pass


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
        pass

    def remove_task(self, task_id: str) -> None:
        """Remove the care task with the given id from this pet."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return all care tasks for this pet."""
        pass


@dataclass
class Owner:
    """The person responsible for the pet's care and the day's constraints."""

    name: str
    available_minutes: int = 0
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def set_available_time(self, minutes: int) -> None:
        """Set how many minutes the owner has available today."""
        pass

    def update_preferences(self, preferences: list[str]) -> None:
        """Replace the owner's care preferences."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return the tasks of every pet this owner has."""
        pass


class Scheduler:
    """Builds one daily care plan across all of an owner's pets, sharing the owner's time."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.scheduled_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []

    def generate_plan(self, on: Optional[date] = None) -> list[Task]:
        """Order the due tasks by priority and fit them into the owner's available time."""
        # Start fresh so calling this twice doesn't duplicate tasks.
        self.scheduled_tasks = []
        self.skipped_tasks = []
        pass

    def explain_plan(self) -> str:
        """Explain why each task was scheduled, ordered, or skipped (call generate_plan first)."""
        pass
