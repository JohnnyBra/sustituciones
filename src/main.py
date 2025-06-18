import sys
import os

# Adjust Python path to include the 'src' directory if running from root or elsewhere.
# This ensures that 'from src.module' imports work correctly.
# If this script is in /app/src and run as `python src/main.py` from /app, this might not be strictly necessary,
# but it adds robustness if run from other locations or if the execution environment is different.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_models import TimeSlot
from src.pdf_parser import parse_teacher_schedule_pdf
from src.schedule_manager import ScheduleManager
from src.substitution_handler import SubstitutionHandler

def load_schedules_interactive(schedule_mgr: ScheduleManager, sub_handler: SubstitutionHandler):
    """Handles the logic for loading schedules from a PDF, used at startup and reload."""
    while True:
        pdf_path = input("Enter the path to the teacher schedule PDF: ")
        if not pdf_path:
            print("PDF path cannot be empty. Please try again or type 'cancel' to return to menu.")
            continue
        if pdf_path.lower() == 'cancel':
            return False # User cancelled loading

        try:
            print(f"Attempting to parse PDF: {pdf_path}...")
            # Ensure the environment is set up for pdfplumber to work if it has complex dependencies
            # For example, ensure any required non-Python libraries for pdfplumber are accessible.
            parsed_schedules = parse_teacher_schedule_pdf(pdf_path)

            if not parsed_schedules:
                print("No schedules were parsed from the PDF. The file might be empty, not a schedule PDF, or in an unexpected format.")
                print("Please check the PDF and the parser's assumptions. Try another path or type 'cancel'.")
                continue # Allow user to try another path

            schedule_mgr.load_schedules(parsed_schedules)

            all_teacher_names = [ts.teacher_name for ts in parsed_schedules if ts.teacher_name]
            if not all_teacher_names:
                print("Warning: No teacher names found in the parsed schedules. Substitution balancing might not work as expected.")

            sub_handler.initialize_substitution_counts(all_teacher_names)
            print(f"Schedules loaded successfully for {len(all_teacher_names)} teachers.")
            print(f"Initial substitution counts (all 0): {sub_handler.get_substitution_counts()}")
            return True # Loading was successful

        except FileNotFoundError:
            print(f"Error: PDF file not found at '{pdf_path}'. Please check the path and try again or type 'cancel'.")
        except Exception as e:
            # Catching general exceptions from pdfplumber or other parts of parsing
            print(f"An error occurred while parsing or loading schedules: {e}")
            print("This could be due to an issue with the PDF file, its format, or an internal error.")
            print("Please check the console for more details from the parser if available.")
            print("Try another path or type 'cancel'.")
        # Loop continues if there was an error, allowing user to re-enter path or cancel.


def main():
    """Main function to run the CLI application."""
    print("Welcome to the Teacher Substitution Management System!")

    schedule_mgr = ScheduleManager()
    sub_handler = SubstitutionHandler()

    # Initial loading of schedules
    if not load_schedules_interactive(schedule_mgr, sub_handler):
        print("No schedules loaded. Exiting program as initial load was cancelled.")
        return

    while True:
        print("\nMenu Options:")
        print("1. Record an absence and find substitute")
        print("2. View substitution counts")
        print("3. Reload schedules from PDF")
        print("4. Exit")

        choice = input("Choose an option (1-4): ")

        if choice == '1':
            absent_teacher_name = input("Enter the name of the absent teacher: ").strip()
            if not absent_teacher_name:
                print("Absent teacher name cannot be empty.")
                continue

            # Check if absent teacher exists in the system
            if not schedule_mgr.get_teacher_schedule(absent_teacher_name):
                print(f"Teacher '{absent_teacher_name}' not found in loaded schedules. Please check the name or reload schedules.")
                continue

            day_of_absence = input("Enter the day of absence (e.g., Monday, Tuesday): ").strip()
            start_time = input("Enter the start time of absence (HH:MM, e.g., 09:00): ").strip()
            end_time = input("Enter the end time of absence (HH:MM, e.g., 10:00): ").strip()

            # Basic validation for inputs (can be expanded)
            if not all([day_of_absence, start_time, end_time]):
                print("Day, start time, and end time cannot be empty.")
                continue

            try:
                # Simple validation for time format (can be more robust)
                if ":" not in start_time or ":" not in end_time:
                    raise ValueError("Time format should be HH:MM")
                # Further validation could check if HH and MM are numbers and in valid ranges.
            except ValueError as ve:
                print(f"Invalid input: {ve}")
                continue

            absence_slot = TimeSlot(day=day_of_absence, start_time=start_time, end_time=end_time)

            print(f"\nSearching for available teachers for {absent_teacher_name} during {absence_slot.day} {absence_slot.start_time}-{absence_slot.end_time}...")
            available_teachers = schedule_mgr.get_available_teachers(absence_slot, absent_teacher_name)

            if not available_teachers:
                print("No available teachers found for this specific time slot with 'reinforcement' or 'guardia' duties.")
                continue

            print(f"Available teachers with 'reinforcement'/'guardia' in this slot: {[t.teacher_name for t in available_teachers]}")

            proposed_substitute = sub_handler.select_substitute(available_teachers)

            if not proposed_substitute:
                print("Could not select a substitute. This might happen if available teachers are not in the substitution count list (e.g., new teachers not in initial PDF) or an internal issue.")
                continue

            print(f"System proposes: {proposed_substitute.teacher_name} (Substitutions: {sub_handler.substitution_counts.get(proposed_substitute.teacher_name, 0)})")

            confirm = input(f"Assign {proposed_substitute.teacher_name}? (yes/no/choose): ").lower().strip()

            assigned_teacher_name = None
            if confirm == 'yes':
                assigned_teacher_name = proposed_substitute.teacher_name
            elif confirm == 'choose':
                print("Available for manual selection:")
                for i, t in enumerate(available_teachers):
                    print(f"  {i+1}. {t.teacher_name} (Substitutions: {sub_handler.substitution_counts.get(t.teacher_name, 'N/A')})")

                while True:
                    try:
                        manual_choice_idx_str = input(f"Enter number of teacher to assign (1-{len(available_teachers)}): ")
                        manual_choice_idx = int(manual_choice_idx_str) - 1
                        if 0 <= manual_choice_idx < len(available_teachers):
                            chosen_teacher = available_teachers[manual_choice_idx]
                            # Check if chosen teacher is in substitution_counts, if not, it's an issue with select_substitute or available_teachers list
                            if chosen_teacher.teacher_name not in sub_handler.substitution_counts:
                                print(f"Warning: Teacher {chosen_teacher.teacher_name} was available but not in substitution tracking. Adding them now.")
                            assigned_teacher_name = chosen_teacher.teacher_name
                            break
                        else:
                            print("Invalid selection number.")
                    except ValueError:
                        print("Please enter a valid number.")
            else: # 'no' or any other input
                print("Substitution cancelled for this slot.")

            if assigned_teacher_name:
                sub_handler.record_substitution(assigned_teacher_name)
                print(f"{assigned_teacher_name} assigned. Substitution counts updated.")
                print(f"Current count for {assigned_teacher_name}: {sub_handler.substitution_counts.get(assigned_teacher_name)}")


        elif choice == '2':
            counts = sub_handler.get_substitution_counts()
            if not counts:
                print("No substitution counts available. Load schedules first or record a substitution.")
            else:
                print("\nSubstitution Counts:")
                # Sort by count for better readability
                sorted_counts = sorted(counts.items(), key=lambda item: item[1])
                for name, count in sorted_counts:
                    print(f"  {name}: {count}")

        elif choice == '3':
            print("\nReloading schedules...")
            # Store current counts in case loading fails and user wants to revert or compare
            # current_counts_backup = sub_handler.get_substitution_counts().copy()
            if load_schedules_interactive(schedule_mgr, sub_handler):
                print("Schedules reloaded.")
            else:
                print("Reload cancelled. Previous schedule data (if any) is still active.")
                # If needed, restore backup: sub_handler.substitution_counts = current_counts_backup

        elif choice == '4':
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid option. Please choose a number between 1 and 4.")

if __name__ == "__main__":
    # This structure helps if other scripts in the future might want to import functions from main.py
    # without automatically running the CLI.
    main()
