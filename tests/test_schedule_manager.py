import unittest
import sys
import os

# Adjust Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.schedule_manager import ScheduleManager
from src.data_models import TeacherSchedule, TimeSlot, ScheduledActivity

class TestScheduleManager(unittest.TestCase):

    def setUp(self):
        """Set up test data and manager instance before each test."""
        self.manager = ScheduleManager()

        # Teacher A: Reinforcement on Monday 09:00-10:00
        self.ts_a_mon_reinforcement = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        self.act_a_mon_reinforcement = ScheduledActivity(activity_name="Guardia", activity_type="reinforcement")
        self.schedule_a = TeacherSchedule(teacher_name="Teacher A", schedule=[(self.ts_a_mon_reinforcement, self.act_a_mon_reinforcement)])

        # Teacher B: Class on Monday 09:00-10:00
        self.ts_b_mon_class = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        self.act_b_mon_class = ScheduledActivity(activity_name="Math Class", activity_type="class")
        self.schedule_b = TeacherSchedule(teacher_name="Teacher B", schedule=[(self.ts_b_mon_class, self.act_b_mon_class)])

        # Teacher C: Reinforcement on Tuesday 09:00-10:00
        self.ts_c_tue_reinforcement = TimeSlot(day="Tuesday", start_time="09:00", end_time="10:00")
        self.act_c_tue_reinforcement = ScheduledActivity(activity_name="Refuerzo Lengua", activity_type="reinforcement")
        self.schedule_c = TeacherSchedule(teacher_name="Teacher C", schedule=[(self.ts_c_tue_reinforcement, self.act_c_tue_reinforcement)])

        # Teacher D: Reinforcement on Monday 09:00-10:00 (same as A) and a class at another time
        self.ts_d_mon_reinforcement = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        self.act_d_mon_reinforcement = ScheduledActivity(activity_name="Guardia", activity_type="reinforcement")
        self.ts_d_mon_class = TimeSlot(day="Monday", start_time="10:00", end_time="11:00")
        self.act_d_mon_class = ScheduledActivity(activity_name="History", activity_type="class")
        self.schedule_d = TeacherSchedule(teacher_name="Teacher D", schedule=[
            (self.ts_d_mon_reinforcement, self.act_d_mon_reinforcement),
            (self.ts_d_mon_class, self.act_d_mon_class)
        ])

        self.manager.load_schedules([self.schedule_a, self.schedule_b, self.schedule_c, self.schedule_d])

    def test_load_schedules(self):
        self.assertIsNotNone(self.manager.get_teacher_schedule("Teacher A"))
        self.assertIsNotNone(self.manager.get_teacher_schedule("Teacher B"))
        self.assertIsNotNone(self.manager.get_teacher_schedule("Teacher C"))
        self.assertIsNotNone(self.manager.get_teacher_schedule("Teacher D"))
        self.assertEqual(len(self.manager.teacher_schedules_map), 4)

    def test_get_teacher_schedule_found(self):
        retrieved_schedule = self.manager.get_teacher_schedule("Teacher A")
        self.assertEqual(retrieved_schedule, self.schedule_a)

    def test_get_teacher_schedule_not_found(self):
        self.assertIsNone(self.manager.get_teacher_schedule("Teacher Z (Non-existent)"))

    def test_get_available_teachers_found_one(self):
        # Teacher B is absent, looking for Monday 09:00-10:00. Teacher A and D should be available.
        # For this specific test, let's assume only Teacher A was loaded to test single availability.
        # We will test multiple available teachers in another test.
        temp_manager = ScheduleManager()
        temp_manager.load_schedules([self.schedule_a, self.schedule_b]) # Only A and B

        target_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        available = temp_manager.get_available_teachers(target_slot, absent_teacher_name="Teacher B")
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].teacher_name, "Teacher A")

    def test_get_available_teachers_found_multiple(self):
        # Teacher B is absent, looking for Mon 09:00-10:00. A and D are available.
        target_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        available = self.manager.get_available_teachers(target_slot, absent_teacher_name="Teacher B")
        self.assertEqual(len(available), 2)
        self.assertIn(self.schedule_a, available)
        self.assertIn(self.schedule_d, available)

    def test_get_available_teachers_none_wrong_time(self):
        # Looking for Mon 10:00-11:00, Teacher D has a class, not reinforcement. No one else.
        target_slot = TimeSlot(day="Monday", start_time="10:00", end_time="11:00")
        available = self.manager.get_available_teachers(target_slot, absent_teacher_name="Teacher A")
        self.assertEqual(len(available), 0)

    def test_get_available_teachers_none_wrong_day(self):
        # Looking for Mon 09:00-10:00, but absent teacher is Teacher C (who is Tue).
        # A and D are available on Mon.
        target_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        available = self.manager.get_available_teachers(target_slot, absent_teacher_name="Teacher C")
        self.assertEqual(len(available), 2) # A and D are available

        # Now look for Tuesday, where C is available
        target_slot_tuesday = TimeSlot(day="Tuesday", start_time="09:00", end_time="10:00")
        available_tuesday = self.manager.get_available_teachers(target_slot_tuesday, absent_teacher_name="Teacher A")
        self.assertEqual(len(available_tuesday), 1)
        self.assertEqual(available_tuesday[0].teacher_name, "Teacher C")


    def test_get_available_teachers_absent_teacher_is_also_available(self):
        # Teacher A is absent. Teacher D is also available at that time.
        # So, Teacher A should not be in the list of available teachers.
        target_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        available = self.manager.get_available_teachers(target_slot, absent_teacher_name="Teacher A")
        self.assertEqual(len(available), 1)
        self.assertNotIn(self.schedule_a, available)
        self.assertEqual(available[0].teacher_name, "Teacher D")

    def test_get_available_teachers_activity_type(self):
        # Teacher B has a 'class' at Mon 09:00-10:00, should not be available for substitution.
        # Teacher A & D have 'reinforcement'.
        target_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        available = self.manager.get_available_teachers(target_slot, absent_teacher_name="Teacher C") # C is irrelevant here

        teacher_names_available = [t.teacher_name for t in available]
        self.assertIn("Teacher A", teacher_names_available)
        self.assertIn("Teacher D", teacher_names_available)
        self.assertNotIn("Teacher B", teacher_names_available) # B has a class, not reinforcement

    def test_get_available_teachers_no_one_available(self):
        target_slot = TimeSlot(day="Friday", start_time="09:00", end_time="10:00") # No one scheduled
        available = self.manager.get_available_teachers(target_slot, absent_teacher_name="Teacher A")
        self.assertEqual(len(available), 0)

    def test_load_schedules_empty(self):
        self.manager.load_schedules([])
        self.assertEqual(len(self.manager.teacher_schedules_map), 0)
        self.assertIsNone(self.manager.get_teacher_schedule("Teacher A"))

if __name__ == '__main__':
    unittest.main()
