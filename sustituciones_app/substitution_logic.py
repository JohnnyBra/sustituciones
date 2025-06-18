# Import load_schedules and load_substitution_counts if you plan to use them directly here for tests.
# For now, the main functions will receive data as arguments.
# from .data_manager import load_schedules, load_substitution_counts

def find_available_teachers(schedules_data, target_day_of_week, target_time_slot):
    """
    Finds teachers who are available (e.g., on 'refuerzo' or 'guardia') for a specific time slot.

    Args:
        schedules_data (list): List of teacher schedule dictionaries.
        target_day_of_week (str): The day to check (e.g., "Lunes").
        target_time_slot (str): The time slot to check (e.g., "08:00-09:00").

    Returns:
        list: A list of teacher names who are available.
    """
    available_teachers = []
    for teacher_info in schedules_data:
        teacher_name = teacher_info.get('teacher_name')
        schedule = teacher_info.get('schedule')
        if not teacher_name or not schedule:
            continue

        day_schedule = schedule.get(target_day_of_week)
        if not day_schedule:
            continue

        for activity in day_schedule:
            if activity.get('time') == target_time_slot:
                activity_type = activity.get('type', '').lower()
                # Define keywords for availability
                if activity_type in ['refuerzo', 'guardia']:
                    available_teachers.append(teacher_name)
                    break # Found availability for this teacher at this time
    return available_teachers

def select_teacher_for_substitution(available_teachers, substitution_counts):
    """
    Selects a teacher for substitution based on the minimum number of substitutions.

    Args:
        available_teachers (list): A list of names of available teachers.
        substitution_counts (dict): A dict of teacher names and their substitution counts.

    Returns:
        str: The name of the selected teacher, or None if no teachers are available.
    """
    if not available_teachers:
        return None

    min_substitutions = float('inf')
    selected_teacher = None

    # Ensure consistent selection if counts are equal by sorting teachers by name
    # This makes testing more predictable.
    for teacher_name in sorted(available_teachers):
        count = substitution_counts.get(teacher_name, 0)
        if count < min_substitutions:
            min_substitutions = count
            selected_teacher = teacher_name
        # If counts are equal, the first one (due to sorted list) is kept.
        # If we need a different tie-breaking rule, it would be implemented here.

    return selected_teacher

def record_substitution(teacher_name, substitution_counts):
    """
    Increments the substitution count for a given teacher.

    Args:
        teacher_name (str): The name of the teacher who performed the substitution.
        substitution_counts (dict): The current substitution counts.

    Returns:
        dict: The updated substitution counts.
    """
    if teacher_name: # Ensure teacher_name is not None
        substitution_counts[teacher_name] = substitution_counts.get(teacher_name, 0) + 1
    return substitution_counts

if __name__ == "__main__":
    print("Testing substitution_logic.py...")

    sample_schedules_data = [
        {
            'teacher_name': 'Profesor Davila',
            'schedule': {
                'Lunes': [
                    {'time': '08:00-09:00', 'subject': 'Matemáticas Avanzadas', 'type': 'clase'},
                    {'time': '09:00-10:00', 'subject': 'Física Cuántica', 'type': 'clase'}
                ],
                'Martes': [
                    {'time': '10:00-11:00', 'subject': 'GUARDIA', 'type': 'guardia'}
                ]
            }
        },
        {
            'teacher_name': 'Profesora Elena',
            'schedule': {
                'Lunes': [
                    {'time': '08:00-09:00', 'subject': 'Literatura Universal', 'type': 'clase'}
                ],
                'Martes': [
                    {'time': '10:00-11:00', 'subject': 'REFUERZO Lengua', 'type': 'refuerzo'},
                    {'time': '11:00-12:00', 'subject': 'Latín', 'type': 'clase'}
                ]
            }
        },
        {
            'teacher_name': 'Profesor Carlos',
            'schedule': {
                'Martes': [
                    {'time': '10:00-11:00', 'subject': 'Educación Física', 'type': 'clase'},
                    {'time': '12:00-13:00', 'subject': 'GUARDIA', 'type': 'guardia'}
                ]
            }
        },
         {
            'teacher_name': 'Profesora Sofia',
            'schedule': {
                'Martes': [
                    {'time': '10:00-11:00', 'subject': 'REFUERZO Matemáticas', 'type': 'refuerzo'}
                ]
            }
        }
    ]

    sample_substitution_counts = {
        'Profesor Davila': 2,
        'Profesora Elena': 5,
        # Profesor Carlos has 0 by default
        'Profesora Sofia': 2
    }

    print("\n--- Test: Finding Available Teachers ---")
    target_day = 'Martes'
    target_time = '10:00-11:00'
    print(f"Looking for teachers available on {target_day} at {target_time}:")

    available = find_available_teachers(sample_schedules_data, target_day, target_time)
    print(f"Available teachers: {available}")
    assert 'Profesor Davila' in available
    assert 'Profesora Elena' in available
    assert 'Profesora Sofia' in available
    assert 'Profesor Carlos' not in available # Carlos has class at that time

    print("\n--- Test: Selecting Teacher for Substitution ---")
    # Expected: Profesor Davila (count 2), Profesora Sofia (count 2). Davila comes first alphabetically.
    # Profesora Elena has count 5.
    print(f"Initial counts: {sample_substitution_counts}")
    print(f"Available for selection: {available}")

    selected = select_teacher_for_substitution(available, sample_substitution_counts)
    print(f"Selected teacher: {selected}")
    assert selected == 'Profesor Davila', f"Expected 'Profesor Davila', got {selected}"

    # Test with an empty list of available teachers
    empty_available = []
    selected_empty = select_teacher_for_substitution(empty_available, sample_substitution_counts)
    print(f"Selected teacher from empty list: {selected_empty}")
    assert selected_empty is None

    # Test with a teacher not yet in counts (should be treated as 0)
    available_with_new = ['Profesor Davila', 'Profesora Elena', 'Profesor Carlos', 'Profesora Sofia'] # Carlos is new for counts
    print(f"Available for selection (incl. Carlos): {available_with_new}")
    selected_new_teacher = select_teacher_for_substitution(available_with_new, sample_substitution_counts)
    print(f"Selected teacher (Carlos should be preferred as count 0): {selected_new_teacher}")
    assert selected_new_teacher == 'Profesor Carlos', f"Expected 'Profesor Carlos', got {selected_new_teacher}"


    print("\n--- Test: Recording Substitution ---")
    if selected: # Use the previously selected teacher if one was found
        print(f"Recording substitution for: {selected}")
        updated_counts = record_substitution(selected, sample_substitution_counts.copy()) # Use copy to preserve original for other tests
        print(f"Original counts for {selected}: {sample_substitution_counts.get(selected, 0)}")
        print(f"Updated counts for {selected}: {updated_counts.get(selected)}")
        assert updated_counts.get(selected) == sample_substitution_counts.get(selected, 0) + 1

        # Record for Carlos (who had 0)
        print(f"Recording substitution for: Profesor Carlos")
        updated_counts_carlos = record_substitution('Profesor Carlos', sample_substitution_counts.copy())
        print(f"Original counts for Profesor Carlos: {sample_substitution_counts.get('Profesor Carlos', 0)}")
        print(f"Updated counts for Profesor Carlos: {updated_counts_carlos.get('Profesor Carlos')}")
        assert updated_counts_carlos.get('Profesor Carlos') == 1
    else:
        print("Skipping record test as no teacher was selected initially.")

    # Test recording for a teacher not previously in counts
    new_teacher_name = "Profesora Nueva"
    print(f"Recording substitution for a new teacher: {new_teacher_name}")
    counts_for_new = {}
    updated_counts_new_teacher = record_substitution(new_teacher_name, counts_for_new)
    print(f"Counts for {new_teacher_name} after first substitution: {updated_counts_new_teacher.get(new_teacher_name)}")
    assert updated_counts_new_teacher.get(new_teacher_name) == 1
    updated_counts_new_teacher = record_substitution(new_teacher_name, updated_counts_new_teacher)
    print(f"Counts for {new_teacher_name} after second substitution: {updated_counts_new_teacher.get(new_teacher_name)}")
    assert updated_counts_new_teacher.get(new_teacher_name) == 2

    print("\nSubstitution logic tests completed.")
