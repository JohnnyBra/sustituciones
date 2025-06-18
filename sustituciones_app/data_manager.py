import json
import os

DATA_DIR = "sustituciones_app/data"

def _ensure_data_dir_exists():
    """Ensures that the data directory exists, creating it if necessary."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_schedules(schedules_data, file_name="horarios.json"):
    """
    Saves schedules data to a JSON file.

    Args:
        schedules_data (list): A list of teacher schedules.
        file_name (str, optional): The name of the file. Defaults to "horarios.json".
    """
    _ensure_data_dir_exists()
    file_path = os.path.join(DATA_DIR, file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(schedules_data, f, indent=4, ensure_ascii=False)
        print(f"Schedules saved to {file_path}")
    except IOError as e:
        print(f"Error saving schedules to {file_path}: {e}")

def load_schedules(file_name="horarios.json"):
    """
    Loads schedules data from a JSON file.

    Args:
        file_name (str, optional): The name of the file. Defaults to "horarios.json".

    Returns:
        list: The loaded schedules data, or an empty list if the file doesn't exist or is invalid.
    """
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {file_path}. Returning empty list.")
        return []
    except IOError as e:
        print(f"Error loading schedules from {file_path}: {e}. Returning empty list.")
        return []

def save_substitution_counts(counts_data, file_name="sustituciones_contador.json"):
    """
    Saves substitution counts to a JSON file.

    Args:
        counts_data (dict): A dictionary of teacher names and their substitution counts.
        file_name (str, optional): The name of the file. Defaults to "sustituciones_contador.json".
    """
    _ensure_data_dir_exists()
    file_path = os.path.join(DATA_DIR, file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(counts_data, f, indent=4, ensure_ascii=False)
        print(f"Substitution counts saved to {file_path}")
    except IOError as e:
        print(f"Error saving substitution counts to {file_path}: {e}")

def load_substitution_counts(file_name="sustituciones_contador.json"):
    """
    Loads substitution counts from a JSON file.

    Args:
        file_name (str, optional): The name of the file. Defaults to "sustituciones_contador.json".

    Returns:
        dict: The loaded substitution counts, or an empty dict if the file doesn't exist or is invalid.
    """
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {file_path}. Returning empty dictionary.")
        return {}
    except IOError as e:
        print(f"Error loading substitution counts from {file_path}: {e}. Returning empty dictionary.")
        return {}

if __name__ == "__main__":
    print("Testing data_manager.py...")

    # Test saving and loading schedules
    sample_schedules = [
        {
            'teacher_name': 'Profesor Alpha',
            'schedule': {'Lunes': [{'time': '08:00-09:00', 'subject': 'Mates', 'type': 'clase'}]}
        },
        {
            'teacher_name': 'Profesora Beta',
            'schedule': {'Martes': [{'time': '10:00-11:00', 'subject': 'Lengua', 'type': 'clase'}]}
        }
    ]
    save_schedules(sample_schedules, "test_horarios.json")
    loaded_schedules = load_schedules("test_horarios.json")
    print("\nLoaded Schedules:")
    if loaded_schedules:
        for schedule in loaded_schedules:
            print(f"  {schedule['teacher_name']}: {schedule['schedule']}")
    else:
        print("  No schedules loaded or file was empty/corrupt.")
    assert loaded_schedules == sample_schedules, "Mismatch in loaded schedules"

    # Test saving and loading substitution counts
    sample_counts = {
        'Profesor Alpha': 3,
        'Profesora Beta': 1,
        'Profesor Gamma': 5
    }
    save_substitution_counts(sample_counts, "test_sustituciones_contador.json")
    loaded_counts = load_substitution_counts("test_sustituciones_contador.json")
    print("\nLoaded Substitution Counts:")
    if loaded_counts:
        for teacher, count in loaded_counts.items():
            print(f"  {teacher}: {count}")
    else:
        print("  No counts loaded or file was empty/corrupt.")
    assert loaded_counts == sample_counts, "Mismatch in loaded counts"

    # Test loading non-existent files
    print("\nTesting loading non-existent files (should return defaults):")
    non_existent_schedules = load_schedules("non_existent_horarios.json")
    assert non_existent_schedules == [], "Non-existent schedule file did not return empty list"
    print(f"  Loading non-existent schedules: {non_existent_schedules} (Expected: [])")

    non_existent_counts = load_substitution_counts("non_existent_contador.json")
    assert non_existent_counts == {}, "Non-existent counts file did not return empty dict"
    print(f"  Loading non-existent counts: {non_existent_counts} (Expected: {{}})")

    # Test creating the data directory
    if os.path.exists(DATA_DIR):
         # Clean up test files and directory if needed for a clean test run
        if os.path.exists(os.path.join(DATA_DIR, "test_horarios.json")):
            os.remove(os.path.join(DATA_DIR, "test_horarios.json"))
        if os.path.exists(os.path.join(DATA_DIR, "test_sustituciones_contador.json")):
            os.remove(os.path.join(DATA_DIR, "test_sustituciones_contador.json"))
        # Potentially remove DATA_DIR if it was created by this test,
        # but be cautious if other processes might use it.
        # For this script, if it's empty, we can try to remove.
        if not os.listdir(DATA_DIR): # Check if empty
            os.rmdir(DATA_DIR)
            print(f"\nCleaned up test files and directory: {DATA_DIR}")
        else:
            print(f"\nTest files removed, but {DATA_DIR} not empty, not removed.")


    print("\nData manager tests completed.")
