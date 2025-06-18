import unittest
import sys
import os

# Adjust Python path to include the project root (parent of 'src' and 'tests')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_models import TimeSlot, ScheduledActivity, TeacherSchedule, SubstitutionLog

class TestDataModels(unittest.TestCase):
    def test_timeslot_creation(self):
        ts = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        self.assertEqual(ts.day, "Monday")
        self.assertEqual(ts.start_time, "09:00")
        self.assertEqual(ts.end_time, "10:00")

    def test_scheduled_activity_creation(self):
        sa = ScheduledActivity(activity_name="Math", activity_type="class")
        self.assertEqual(sa.activity_name, "Math")
        self.assertEqual(sa.activity_type, "class")

    def test_teacher_schedule_creation(self):
        ts_obj = TimeSlot(day="Tuesday", start_time="10:00", end_time="11:00")
        sa_obj = ScheduledActivity(activity_name="Physics", activity_type="class")
        teacher_sched = TeacherSchedule(teacher_name="Mr. Test", schedule=[(ts_obj, sa_obj)])
        self.assertEqual(teacher_sched.teacher_name, "Mr. Test")
        self.assertEqual(len(teacher_sched.schedule), 1)
        self.assertEqual(teacher_sched.schedule[0][0], ts_obj)
        self.assertEqual(teacher_sched.schedule[0][1], sa_obj)

    def test_substitution_log_creation(self):
        ts_obj = TimeSlot(day="Wednesday", start_time="11:00", end_time="12:00")
        log_entry = SubstitutionLog(
            substituting_teacher_name="Mrs. Substitute",
            absent_teacher_name="Mr. Absent",
            date="2023-10-26",
            time_slot=ts_obj
        )
        self.assertEqual(log_entry.substituting_teacher_name, "Mrs. Substitute")
        self.assertEqual(log_entry.absent_teacher_name, "Mr. Absent")
        self.assertEqual(log_entry.date, "2023-10-26")
        self.assertEqual(log_entry.time_slot, ts_obj)

if __name__ == '__main__':
    unittest.main()
