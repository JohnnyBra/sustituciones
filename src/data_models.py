from dataclasses import dataclass, field
from typing import List, Tuple, Dict

@dataclass
class TimeSlot:
    """Represents a time slot with a day, start time, and end time."""
    day: str
    start_time: str
    end_time: str

@dataclass
class ScheduledActivity:
    """Represents an activity scheduled for a time slot."""
    activity_name: str
    activity_type: str  # e.g., 'class', 'reinforcement', 'break'

@dataclass
class TeacherSchedule:
    """Represents a teacher's schedule."""
    teacher_name: str
    # Using a list of tuples: (TimeSlot, ScheduledActivity)
    schedule: List[Tuple[TimeSlot, ScheduledActivity]] = field(default_factory=list)

@dataclass
class SubstitutionLog:
    """Represents a log entry for a teacher substitution."""
    substituting_teacher_name: str
    absent_teacher_name: str
    date: str  # Using str for simplicity, can be changed to datetime.date later
    time_slot: TimeSlot
