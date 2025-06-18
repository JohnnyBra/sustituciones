from typing import Dict, List, Optional
from src.data_models import TeacherSchedule # Assuming TeacherSchedule has a teacher_name attribute

class SubstitutionHandler:
    """
    Manages the selection of substitute teachers based on substitution counts
    to ensure fair distribution of substitution duties.
    """

    def __init__(self):
        """
        Initializes the SubstitutionHandler with an empty dictionary to track
        substitution counts for each teacher.
        """
        self.substitution_counts: Dict[str, int] = {}

    def initialize_substitution_counts(self, teacher_names: List[str]):
        """
        Resets and initializes substitution counts for a list of teacher names.
        All teachers in the list will have their count set to 0.

        Args:
            teacher_names: A list of teacher names to initialize counts for.
        """
        self.substitution_counts.clear()
        for name in teacher_names:
            if name: # Ensure name is not empty or None
                self.substitution_counts[name] = 0
            else:
                print("Warning: Skipping an empty or None teacher name during count initialization.")

    def select_substitute(self, available_teachers: List[TeacherSchedule]) -> Optional[TeacherSchedule]:
        """
        Selects the most appropriate substitute teacher from a list of available
        teachers. The selection is based on minimizing the substitution count.

        Args:
            available_teachers: A list of TeacherSchedule objects for teachers
                                who are available for substitution.

        Returns:
            The TeacherSchedule object of the selected substitute teacher, or None
            if no suitable teacher is found.
        """
        if not available_teachers:
            return None

        # Filter to include only teachers whose counts are being tracked.
        # This assumes initialize_substitution_counts was called with all relevant teachers.
        eligible_teachers = [
            teacher for teacher in available_teachers
            if teacher.teacher_name in self.substitution_counts
        ]

        if not eligible_teachers:
            print("Warning: No available teachers are currently tracked for substitution counts.")
            # This could happen if available_teachers contains names not passed to initialize_substitution_counts
            return None

        # Sort teachers by their substitution count (ascending).
        # Teachers not in substitution_counts (though filtered above) would default to infinity if not handled.
        sorted_teachers = sorted(
            eligible_teachers,
            key=lambda teacher: self.substitution_counts.get(teacher.teacher_name, float('inf'))
        )

        return sorted_teachers[0] if sorted_teachers else None

    def record_substitution(self, teacher_name: str):
        """
        Increments the substitution count for a given teacher.

        If the teacher is not currently tracked, their count will be initialized to 1.
        It's generally expected that teachers are initialized via
        `initialize_substitution_counts`.

        Args:
            teacher_name: The name of the teacher who performed the substitution.
        """
        if not teacher_name:
            print("Warning: Attempted to record substitution for an empty or None teacher name.")
            return

        self.substitution_counts[teacher_name] = self.substitution_counts.get(teacher_name, 0) + 1

    def get_substitution_counts(self) -> Dict[str, int]:
        """
        Returns the current substitution counts for all tracked teachers.

        Returns:
            A dictionary where keys are teacher names and values are their
            respective substitution counts.
        """
        return self.substitution_counts

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    print("This script is intended to be imported as a module.")
    print("Example usage below (requires data_models to be in PYTHONPATH):")

    # Dummy TeacherSchedule objects (only teacher_name is relevant for this handler's logic)
    teacher_alice = TeacherSchedule(teacher_name="Alice", schedule=[])
    teacher_bob = TeacherSchedule(teacher_name="Bob", schedule=[])
    teacher_carol = TeacherSchedule(teacher_name="Carol", schedule=[])
    teacher_dave = TeacherSchedule(teacher_name="Dave", schedule=[]) # Not initialized in counts

    handler = SubstitutionHandler()
    handler.initialize_substitution_counts(["Alice", "Bob", "Carol"])
    print(f"Initial counts: {handler.get_substitution_counts()}")

    # Scenario 1: Alice and Bob are available
    available1 = [teacher_alice, teacher_bob]
    sub1 = handler.select_substitute(available1)
    if sub1:
        print(f"Selected substitute: {sub1.teacher_name}") # Expected: Alice or Bob (depends on dict order before sort)
        handler.record_substitution(sub1.teacher_name)
    print(f"Counts after 1st sub: {handler.get_substitution_counts()}")

    # Scenario 2: Bob and Carol are available. Bob was sub1 if Alice was picked first, or vice versa.
    # Let's assume Alice was picked. So Alice=1, Bob=0, Carol=0.
    # If Bob was picked, then Alice=0, Bob=1, Carol=0

    # To make it deterministic for example:
    # Let's say Alice was picked (count becomes 1 for Alice)
    # Now Bob (0) and Carol (0) are available.
    if sub1 and sub1.teacher_name == "Alice": # If Alice was picked
        pass # Counts are Alice:1, Bob:0, Carol:0
    elif sub1 and sub1.teacher_name == "Bob": # If Bob was picked
        pass # Counts are Alice:0, Bob:1, Carol:0
    # For the sake of example, let's manually set one to make next step predictable
    # handler.substitution_counts["Alice"] = 1
    # print(f"Manually setting Alice's count to 1 for predictable example: {handler.get_substitution_counts()}")


    available2 = [teacher_bob, teacher_carol]
    sub2 = handler.select_substitute(available2)
    if sub2:
        print(f"Selected substitute: {sub2.teacher_name}") # Expected: Bob or Carol (the one with 0)
        handler.record_substitution(sub2.teacher_name)
    print(f"Counts after 2nd sub: {handler.get_substitution_counts()}")

    # Scenario 3: All three are available. One has 1, other has 1, last has 0.
    # e.g. Alice=1, Bob=1, Carol=0 (if order was Alice then Bob)
    available3 = [teacher_alice, teacher_bob, teacher_carol]
    sub3 = handler.select_substitute(available3)
    if sub3:
        print(f"Selected substitute: {sub3.teacher_name}") # Expected: The one with the lowest count
        handler.record_substitution(sub3.teacher_name)
    print(f"Counts after 3rd sub: {handler.get_substitution_counts()}")

    # Scenario 4: Teacher Dave (not initialized) and Alice are available
    available4 = [teacher_dave, teacher_alice]
    sub4 = handler.select_substitute(available4)
    if sub4:
        print(f"Selected substitute (Dave not initialized): {sub4.teacher_name}") # Expected: Alice
        handler.record_substitution(sub4.teacher_name)
    else:
        print("No substitute selected as expected (Dave not in counts).")
    print(f"Counts after 4th scenario: {handler.get_substitution_counts()}")

    # Scenario 5: Record substitution for Dave (who wasn't initialized)
    print("Recording substitution for Dave (not initially in counts):")
    handler.record_substitution("Dave")
    print(f"Counts after Dave's sub: {handler.get_substitution_counts()}") # Expected: Dave:1

    # Scenario 6: No teachers available
    available5 = []
    sub5 = handler.select_substitute(available5)
    if not sub5:
        print("No substitute selected (no one available), as expected.")

    # Scenario 7: Available teacher not in initialized list
    teacher_eve = TeacherSchedule(teacher_name="Eve", schedule=[])
    available6 = [teacher_eve]
    sub6 = handler.select_substitute(available6)
    if not sub6:
        print("No substitute selected (Eve not in counts and no other options), as expected.")

    print(f"Final counts: {handler.get_substitution_counts()}")
