import pdfplumber
from src.data_models import TeacherSchedule, TimeSlot, ScheduledActivity
from typing import List

# Keywords to identify activity type. Case-insensitive.
REINFORCEMENT_KEYWORDS = ["REFUERZO", "GUARDIA"]

# Days of the week corresponding to table columns (after the time column)
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def parse_teacher_schedule_pdf(pdf_path: str) -> List[TeacherSchedule]:
    """
    Parses a PDF file containing teacher schedules.

    Assumptions:
    - Each page (or a significant portion of it) represents one teacher's schedule.
    - The teacher's name is assumed to be the first significant text block found
      on the page before any tables.
    - The main schedule is contained within the first table extracted from each page.
    - The schedule table has a specific structure:
        - The first row is a header and is skipped.
        - The first column contains time ranges (e.g., "08:00-09:00").
        - The next 5 columns represent Monday to Friday.
    - Cell content directly maps to activity_name.
    - Activity type is 'reinforcement' if activity_name contains keywords like
      "REFUERZO" or "GUARDIA" (case-insensitive), otherwise it's 'class'.
    """
    all_teacher_schedules: List[TeacherSchedule] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # --- Teacher Name Extraction ---
                # Assumption: Teacher's name is the first text extracted before tables.
                # This is a very strong assumption and likely needs refinement.
                page_text_elements = page.extract_text_elements()
                teacher_name = f"Unknown Teacher - Page {page_num + 1}" # Default
                if page_text_elements:
                    # Attempt to find text that is likely a name (heuristic)
                    # For now, concatenating first few lines of text, if they appear before a table.
                    # This needs a more robust heuristic.
                    potential_name_parts = []
                    for element in page_text_elements:
                        # A simple heuristic: stop if we likely hit table data (e.g. numbers, short codes)
                        # This is very basic. A more robust method would be to get all text *before* page.tables[0].bbox if a table exists.
                        if element.y0 < (page.tables[0].bbox[1] if page.tables else page.height * 0.2): # Heuristic: text in top 20% or before table
                             if element.text.strip(): # Ignore empty strings
                                potential_name_parts.append(element.text.strip())
                        else:
                            break # Stop if we are past the assumed name area or table start
                    if potential_name_parts:
                        teacher_name = " ".join(potential_name_parts[:3]) # Take first 3 parts as potential name
                    elif page.extract_text(): # Fallback to first line of text if element extraction is tricky
                         teacher_name = page.extract_text().split('\n')[0].strip()


                # --- Table Extraction ---
                # Assumption: The first table on the page is the schedule.
                tables = page.extract_tables()
                if not tables:
                    # If no tables, create a schedule with this teacher name but no activities
                    # Or decide to skip if a page with no table is not a schedule
                    print(f"Warning: No tables found on page {page_num + 1} for teacher '{teacher_name}'. Skipping page for schedule content.")
                    # Add a TeacherSchedule with an empty schedule if that's desired
                    # teacher_schedule_obj = TeacherSchedule(teacher_name=teacher_name, schedule=[])
                    # all_teacher_schedules.append(teacher_schedule_obj)
                    continue

                # Assuming the first table is the one we want
                schedule_table = tables[0]

                teacher_schedule_activities = []

                # --- Table Parsing (Strong Assumptions) ---
                # Skip header row (assuming it's the first row)
                for row_idx, row in enumerate(schedule_table[1:]):
                    if not row or not row[0]:  # Skip empty rows or rows without a time slot
                        print(f"Warning: Skipping empty or invalid row {row_idx+1} on page {page_num+1}.")
                        continue

                    time_str = row[0].strip() if row[0] else ""
                    if not time_str or '-' not in time_str:
                        print(f"Warning: Invalid time format in row {row_idx+1}, cell 0: '{time_str}' on page {page_num+1}. Skipping row.")
                        continue

                    try:
                        start_time, end_time = time_str.split('-', 1)
                    except ValueError:
                        print(f"Warning: Could not parse time string '{time_str}' in row {row_idx+1} on page {page_num+1}. Skipping row.")
                        continue

                    # Iterate through columns for days (Monday to Friday)
                    # Assumes row[0] is time, row[1] is Mon, ..., row[5] is Fri
                    for day_idx, cell_content in enumerate(row[1:6]): # Columns 1 to 5 for days
                        if cell_content and cell_content.strip():
                            activity_name = cell_content.strip()

                            # Determine day of the week
                            day = DAYS_OF_WEEK[day_idx] if day_idx < len(DAYS_OF_WEEK) else f"Unknown Day {day_idx+1}"

                            time_slot_obj = TimeSlot(
                                day=day,
                                start_time=start_time.strip(),
                                end_time=end_time.strip()
                            )

                            # Determine activity_type
                            activity_type = 'class' # Default
                            for keyword in REINFORCEMENT_KEYWORDS:
                                if keyword.lower() in activity_name.lower():
                                    activity_type = 'reinforcement'
                                    break

                            scheduled_activity_obj = ScheduledActivity(
                                activity_name=activity_name,
                                activity_type=activity_type
                            )
                            teacher_schedule_activities.append((time_slot_obj, scheduled_activity_obj))

                teacher_schedule_obj = TeacherSchedule(
                    teacher_name=teacher_name,
                    schedule=teacher_schedule_activities
                )
                all_teacher_schedules.append(teacher_schedule_obj)

    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        # Depending on desired robustness, you might re-raise, return partial data, or an empty list.
        # For now, returning what has been processed so far.

    return all_teacher_schedules

if __name__ == '__main__':
    # This is a placeholder for testing.
    # You would replace "path/to/your/schedule.pdf" with an actual PDF path.
    # Create a dummy PDF or use a real one for testing this parser.
    print("This script is intended to be imported as a module.")
    print("To test, you would call: parse_teacher_schedule_pdf('path/to/your/schedule.pdf')")

    # Example of how to create a dummy TeacherSchedule for testing purposes if you don't have a PDF yet
    # ts1 = TimeSlot(day="Monday", start_time="08:00", end_time="09:00")
    # sa1 = ScheduledActivity(activity_name="Math 101", activity_type="class")
    # teacher1_sched = TeacherSchedule(teacher_name="Dr. Smith", schedule=[(ts1, sa1)])
    # print(teacher1_sched)

    # To effectively test, you'll need a sample PDF.
    # For now, we'll just ensure the script is syntactically valid.
    pass
