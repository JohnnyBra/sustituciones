import json
import os

DATA_DIR = "sustituciones_app/data"
SCHEDULES_FILE_NAME = "horarios.json"
COUNTS_FILE_NAME = "sustituciones_contador.json"
HISTORY_FILE_NAME = "historial_sustituciones.json"


def _ensure_data_dir_exists():
    """Ensures that the data directory exists, creating it if necessary."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_schedules(schedules_data, file_name=SCHEDULES_FILE_NAME): # Default to constant
    _ensure_data_dir_exists()
    file_path = os.path.join(DATA_DIR, file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(schedules_data, f, indent=4, ensure_ascii=False)
        # print(f"Schedules saved to {file_path}") # Quieter during tests
    except IOError as e:
        print(f"Error saving schedules to {file_path}: {e}")

def load_schedules(file_name=SCHEDULES_FILE_NAME): # Default to constant
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        # print(f"Error decoding JSON from {file_path}. Returning empty list.")
        return []
    except IOError as e:
        # print(f"Error loading schedules from {file_path}: {e}. Returning empty list.")
        return []

def save_substitution_counts(counts_data, file_name=COUNTS_FILE_NAME): # Default to constant
    _ensure_data_dir_exists()
    file_path = os.path.join(DATA_DIR, file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(counts_data, f, indent=4, ensure_ascii=False)
        # print(f"Substitution counts saved to {file_path}") # Quieter during tests
    except IOError as e:
        print(f"Error saving substitution counts to {file_path}: {e}")

def load_substitution_counts(file_name=COUNTS_FILE_NAME): # Default to constant
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        # print(f"Error decoding JSON from {file_path}. Returning empty dictionary.")
        return {}
    except IOError as e:
        # print(f"Error loading substitution counts from {file_path}: {e}. Returning empty dictionary.")
        return {}

def load_substitution_history():
    _ensure_data_dir_exists()
    history_file_path = os.path.join(DATA_DIR, HISTORY_FILE_NAME)
    if not os.path.exists(history_file_path):
        return []
    try:
        with open(history_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading or decoding history file {history_file_path}: {e}. Returning empty list.")
        return []

def append_to_substitution_history(new_substitution_record):
    _ensure_data_dir_exists()
    history_file_path = os.path.join(DATA_DIR, HISTORY_FILE_NAME)

    current_history = load_substitution_history()
    if not isinstance(current_history, list):
        print(f"Warning: History data from {history_file_path} was not a list. Re-initializing history.")
        current_history = []

    current_history.append(new_substitution_record)

    try:
        with open(history_file_path, 'w', encoding='utf-8') as f:
            json.dump(current_history, f, indent=4, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error writing to history file {history_file_path}: {e}")
        return False

if __name__ == "__main__":
    print("Testing data_manager.py...")

    # Test saving and loading schedules
    sample_schedules_data = [
        {'teacher_name': 'Profesor Alpha', 'schedule': {'Lunes': [{'time': '08:00-09:00', 'subject': 'Mates', 'type': 'clase'}]}},
        {'teacher_name': 'Profesora Beta', 'schedule': {'Martes': [{'time': '10:00-11:00', 'subject': 'Lengua', 'type': 'clase'}]}}
    ]
    test_schedules_filename = "test_horarios.json"
    save_schedules(sample_schedules_data, test_schedules_filename)
    loaded_schedules = load_schedules(test_schedules_filename)
    print("\nLoaded Schedules Test:")
    assert loaded_schedules == sample_schedules_data, "Mismatch in loaded schedules"
    print("  Schedules save/load: OK")

    # Test saving and loading substitution counts
    sample_counts_data = {'Profesor Alpha': 3, 'Profesora Beta': 1, 'Profesor Gamma': 5}
    test_counts_filename = "test_sustituciones_contador.json"
    save_substitution_counts(sample_counts_data, test_counts_filename)
    loaded_counts = load_substitution_counts(test_counts_filename)
    print("\nLoaded Substitution Counts Test:")
    assert loaded_counts == sample_counts_data, "Mismatch in loaded counts"
    print("  Counts save/load: OK")

    # Test loading non-existent files
    print("\nTesting loading non-existent files (should return defaults):")
    non_existent_schedules = load_schedules("non_existent_horarios.json")
    assert non_existent_schedules == [], "Non-existent schedule file did not return empty list"
    print(f"  Loading non-existent schedules: OK (Got: {non_existent_schedules})")

    non_existent_counts = load_substitution_counts("non_existent_contador.json")
    assert non_existent_counts == {}, "Non-existent counts file did not return empty dict"
    print(f"  Loading non-existent counts: OK (Got: {non_existent_counts})")

    # Test History Functions
    print("\nTesting History Functions...")
    # Use default HISTORY_FILE_NAME for these tests, ensure it's clean first
    default_history_path = os.path.join(DATA_DIR, HISTORY_FILE_NAME)
    if os.path.exists(default_history_path):
        os.remove(default_history_path)

    initial_history = load_substitution_history()
    print(f"  Initial history (should be empty): {initial_history}")
    assert initial_history == [], "Initial history was not empty!"

    test_record_1 = {"id": 1, "profesor_sustituto": "Profesor Test A", "numero_slots": 1}
    append_to_substitution_history(test_record_1)
    test_record_2 = {"id": 2, "profesor_sustituto": "Profesor Test B", "numero_slots": 2}
    append_to_substitution_history(test_record_2)

    updated_history = load_substitution_history()
    print(f"  Updated history (should have 2 records): {updated_history}")
    assert len(updated_history) == 2
    assert updated_history[0]['profesor_sustituto'] == "Profesor Test A"
    assert updated_history[1]['numero_slots'] == 2
    print("  History append/load: OK")

    # Clean up test files
    print("\nCleaning up test files...")
    files_to_clean = [test_schedules_filename, test_counts_filename, HISTORY_FILE_NAME]
    for f_name in files_to_clean:
        f_path = os.path.join(DATA_DIR, f_name)
        if os.path.exists(f_path):
            os.remove(f_path)
            print(f"  Removed: {f_path}")

    # Attempt to remove DATA_DIR if empty
    if os.path.exists(DATA_DIR) and not os.listdir(DATA_DIR):
        try:
            os.rmdir(DATA_DIR)
            print(f"  Cleaned up directory: {DATA_DIR}")
        except OSError as e:
            print(f"  Could not remove {DATA_DIR}: {e}")
    else:
        if os.path.exists(DATA_DIR):
            print(f"  {DATA_DIR} not empty or not removed by test script.")

    print("\nData manager tests completed.")
