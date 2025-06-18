from typing import Dict, List, Optional
from src.data_models import TeacherSchedule, TimeSlot, ScheduledActivity

class ScheduleManager:
    """Manages teacher schedules and helps find available teachers for substitution."""

    def __init__(self):
        """Initializes the ScheduleManager with an empty map for teacher schedules."""
        self.teacher_schedules_map: Dict[str, TeacherSchedule] = {}

    def load_schedules(self, teacher_schedules: List[TeacherSchedule]):
        """
        Loads a list of TeacherSchedule objects into the manager.

        This will clear any existing schedules.
        The schedules are stored in a dictionary mapping teacher names to their
        TeacherSchedule objects.
        """
        self.teacher_schedules_map.clear()
        for ts in teacher_schedules:
            if ts.teacher_name: # Ensure teacher_name is not empty or None
                self.teacher_schedules_map[ts.teacher_name] = ts
            else:
                print(f"Warning: Skipping a TeacherSchedule object due to missing teacher_name.")

    def get_teacher_schedule(self, teacher_name: str) -> Optional[TeacherSchedule]:
        """
        Retrieves the schedule for a specific teacher.

        Args:
            teacher_name: The name of the teacher.

        Returns:
            The TeacherSchedule object if found, otherwise None.
        """
        return self.teacher_schedules_map.get(teacher_name)

    def get_available_teachers(self, time_slot: TimeSlot, absent_teacher_name: str) -> List[TeacherSchedule]:
        """
        Finds teachers who are available (i.e., have a 'reinforcement' activity)
        during a specific time slot, excluding the absent teacher.

        Args:
            time_slot: The TimeSlot object to check for availability.
            absent_teacher_name: The name of the teacher who is absent.

        Returns:
            A list of TeacherSchedule objects for teachers who are available.
        """
        available_teachers: List[TeacherSchedule] = []
        for teacher_name, teacher_schedule in self.teacher_schedules_map.items():
            if teacher_name == absent_teacher_name:
                continue  # Skip the absent teacher

            is_available_in_slot = False
            for slot, activity in teacher_schedule.schedule:
                # Check if the time slot matches exactly
                if (slot.day == time_slot.day and
                    slot.start_time == time_slot.start_time and
                    slot.end_time == time_slot.end_time):

                    # Check if the activity type is 'reinforcement'
                    if activity.activity_type == 'reinforcement':
                        is_available_in_slot = True
                        break  # Teacher is available in this slot, no need to check further activities

            if is_available_in_slot:
                available_teachers.append(teacher_schedule)

        return available_teachers

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    print("This script is intended to be imported as a module.")
    print("Example usage below (requires data_models to be in PYTHONPATH):")

    # Create some dummy data
    ts1_slot1 = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
    ts1_activity1 = ScheduledActivity(activity_name="Guardia", activity_type="reinforcement")
    teacher1_schedule = TeacherSchedule(teacher_name="Teacher Alice", schedule=[(ts1_slot1, ts1_activity1)])

    ts2_slot1 = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
    ts2_activity1 = ScheduledActivity(activity_name="Math Class", activity_type="class")
    teacher2_schedule = TeacherSchedule(teacher_name="Teacher Bob", schedule=[(ts2_slot1, ts2_activity1)])

    ts3_slot1 = TimeSlot(day="Monday", start_time="10:00", end_time="11:00") # Different time
    ts3_activity1 = ScheduledActivity(activity_name="Guardia", activity_type="reinforcement")
    teacher3_schedule = TeacherSchedule(teacher_name="Teacher Carol", schedule=[(ts3_slot1, ts3_activity1)])

    ts4_slot1 = TimeSlot(day="Monday", start_time="09:00", end_time="10:00") # Same slot as Alice/Bob
    ts4_activity1 = ScheduledActivity(activity_name="REFUERZO LENGUA", activity_type="reinforcement")
    teacher4_schedule = TeacherSchedule(teacher_name="Teacher Dave", schedule=[(ts4_slot1, ts4_activity1)])


    manager = ScheduleManager()
    manager.load_schedules([teacher1_schedule, teacher2_schedule, teacher3_schedule, teacher4_schedule])

    # Test get_teacher_schedule
    print(f"Schedule for Teacher Alice: {manager.get_teacher_schedule('Teacher Alice')}")
    print(f"Schedule for Teacher Eve (non-existent): {manager.get_teacher_schedule('Teacher Eve')}")

    # Test get_available_teachers
    # Teacher Bob is absent, looking for someone for Monday 09:00-10:00
    absent_teacher = "Teacher Bob"
    target_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")

    available = manager.get_available_teachers(target_slot, absent_teacher)
    print(f"\nAvailable teachers for {target_slot} when {absent_teacher} is absent:")
    for teacher in available:
        print(f"- {teacher.teacher_name}") # Expected: Teacher Alice, Teacher Dave

    # Test with a different slot or absent teacher
    absent_teacher_2 = "Teacher Alice"
    available_2 = manager.get_available_teachers(target_slot, absent_teacher_2)
    print(f"\nAvailable teachers for {target_slot} when {absent_teacher_2} is absent:")
    for teacher in available_2:
        print(f"- {teacher.teacher_name}") # Expected: Teacher Dave

    # Test with a slot where no one with 'reinforcement' is available
    target_slot_no_reinforcement = TimeSlot(day="Tuesday", start_time="09:00", end_time="10:00")
    available_3 = manager.get_available_teachers(target_slot_no_reinforcement, "Teacher Bob")
    print(f"\nAvailable teachers for {target_slot_no_reinforcement} (expecting none):")
    for teacher in available_3:
        print(f"- {teacher.teacher_name}") # Expected: None
    if not available_3:
        print("None, as expected.")
