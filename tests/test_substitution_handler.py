import unittest
import sys
import os

# Adjust Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.substitution_handler import SubstitutionHandler
from src.data_models import TeacherSchedule # Only for type hinting, Schedule obj itself is not deeply used by handler

class TestSubstitutionHandler(unittest.TestCase):

    def setUp(self):
        """Set up test data and handler instance before each test."""
        self.handler = SubstitutionHandler()

        # Mock TeacherSchedule objects (only teacher_name is strictly needed by SubstitutionHandler)
        self.teacher_x_schedule = TeacherSchedule(teacher_name="Teacher X", schedule=[])
        self.teacher_y_schedule = TeacherSchedule(teacher_name="Teacher Y", schedule=[])
        self.teacher_z_schedule = TeacherSchedule(teacher_name="Teacher Z", schedule=[])
        self.teacher_untracked_schedule = TeacherSchedule(teacher_name="Teacher Untracked", schedule=[])

        self.teacher_names = ["Teacher X", "Teacher Y", "Teacher Z"]
        self.handler.initialize_substitution_counts(self.teacher_names)

    def test_initialize_substitution_counts(self):
        counts = self.handler.get_substitution_counts()
        self.assertEqual(len(counts), 3)
        self.assertEqual(counts["Teacher X"], 0)
        self.assertEqual(counts["Teacher Y"], 0)
        self.assertEqual(counts["Teacher Z"], 0)

        # Test re-initialization
        self.handler.initialize_substitution_counts(["New Teacher 1", "New Teacher 2"])
        new_counts = self.handler.get_substitution_counts()
        self.assertEqual(len(new_counts), 2)
        self.assertEqual(new_counts["New Teacher 1"], 0)
        self.assertNotIn("Teacher X", new_counts)


    def test_record_substitution(self):
        self.handler.record_substitution("Teacher X")
        counts = self.handler.get_substitution_counts()
        self.assertEqual(counts["Teacher X"], 1)
        self.assertEqual(counts["Teacher Y"], 0) # Should remain unchanged

        self.handler.record_substitution("Teacher X") # Record again
        counts = self.handler.get_substitution_counts()
        self.assertEqual(counts["Teacher X"], 2)

        # Test recording for a teacher not initially in counts (robust get)
        self.handler.record_substitution("Teacher New")
        counts = self.handler.get_substitution_counts()
        self.assertEqual(counts["Teacher New"], 1)
        self.assertEqual(len(counts), 4) # X, Y, Z, New

    def test_select_substitute_empty_available(self):
        selected = self.handler.select_substitute([])
        self.assertIsNone(selected)

    def test_select_substitute_single_available_tracked(self):
        available = [self.teacher_x_schedule]
        selected = self.handler.select_substitute(available)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.teacher_name, "Teacher X")

    def test_select_substitute_single_available_untracked(self):
        # Teacher Untracked was not in initialize_substitution_counts
        available = [self.teacher_untracked_schedule]
        selected = self.handler.select_substitute(available)
        # Expect None because they are filtered out as they are not in self.substitution_counts
        self.assertIsNone(selected, "Should not select a teacher not in substitution_counts")


    def test_select_substitute_balancing(self):
        self.handler.record_substitution("Teacher Y") # Y has 1, X and Z have 0

        # Both X and Y available, X should be chosen (0 vs 1)
        available1 = [self.teacher_x_schedule, self.teacher_y_schedule]
        selected1 = self.handler.select_substitute(available1)
        self.assertEqual(selected1.teacher_name, "Teacher X")
        self.handler.record_substitution(selected1.teacher_name) # X is now 1

        # X=1, Y=1, Z=0. Now Z should be chosen.
        available2 = [self.teacher_x_schedule, self.teacher_y_schedule, self.teacher_z_schedule]
        selected2 = self.handler.select_substitute(available2)
        self.assertEqual(selected2.teacher_name, "Teacher Z")
        self.handler.record_substitution(selected2.teacher_name) # Z is now 1

        # X=1, Y=1, Z=1. Order might be dict-dependent, but one is chosen.
        # Let's make Y have more explicitly.
        self.handler.record_substitution("Teacher Y") # Y is now 2
        # X=1, Y=2, Z=1. X or Z should be chosen.
        available3 = [self.teacher_x_schedule, self.teacher_y_schedule, self.teacher_z_schedule]
        selected3 = self.handler.select_substitute(available3)
        self.assertIn(selected3.teacher_name, ["Teacher X", "Teacher Z"])

    def test_select_substitute_all_same_counts(self):
        # All have 0 counts. The first one in the sorted list (after filtering) should be picked.
        # The order from `available_teachers` might influence if sorting is stable and keys are equal.
        available = [self.teacher_z_schedule, self.teacher_x_schedule, self.teacher_y_schedule]
        selected = self.handler.select_substitute(available)
        # Based on current implementation (sorted by name as a secondary factor if counts are equal,
        # or by original order if sort is stable), we expect one of them.
        # For robustness, we just check if one is selected.
        self.assertIsNotNone(selected)
        self.assertIn(selected.teacher_name, ["Teacher X", "Teacher Y", "Teacher Z"])


    def test_select_substitute_mix_tracked_and_untracked(self):
        self.handler.record_substitution("Teacher X") # X has 1, Y and Z have 0

        available = [self.teacher_untracked_schedule, self.teacher_y_schedule, self.teacher_x_schedule]
        selected = self.handler.select_substitute(available)

        # Teacher Y should be selected (count 0), X has 1, Untracked is ignored.
        self.assertIsNotNone(selected)
        self.assertEqual(selected.teacher_name, "Teacher Y")

    def test_get_substitution_counts_direct_return(self):
        self.handler.record_substitution("Teacher X")
        counts_internal = self.handler.substitution_counts
        counts_method = self.handler.get_substitution_counts()
        self.assertIs(counts_method, counts_internal, "Should return a direct reference to the internal dict")
        self.assertEqual(counts_method["Teacher X"], 1)

    def test_initialize_with_empty_list(self):
        self.handler.initialize_substitution_counts([])
        self.assertEqual(len(self.handler.get_substitution_counts()), 0)

        available = [self.teacher_x_schedule] # X was part of original setup, but now counts are empty
        selected = self.handler.select_substitute(available)
        self.assertIsNone(selected, "No teacher should be selected if counts are not initialized for them.")

if __name__ == '__main__':
    unittest.main()
