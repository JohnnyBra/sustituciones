import fitz  # PyMuPDF
import re
from datetime import datetime, timedelta

# Define las franjas horarias válidas de 30 minutos para la lógica de procesamiento
# Esto debe coincidir con lo que se usa en la aplicación (app.py)
VALID_30_MIN_SLOTS = [
    '09:00-09:30', '09:30-10:00',
    '10:00-10:30', '10:30-11:00',
    # Descanso 11:00-11:30
    '11:30-12:00', '12:00-12:30',
    '12:30-13:00', '13:00-13:30',
    '13:30-14:00'
]
# Crear un set para búsquedas rápidas
VALID_30_MIN_SLOTS_SET = set(VALID_30_MIN_SLOTS)

# Hora de inicio del descanso y hora de fin del descanso
BREAK_START_TIME = datetime.strptime("11:00", "%H:%M").time()
BREAK_END_TIME = datetime.strptime("11:30", "%H:%M").time()

def _parse_time_str(time_str):
    """Parsea HH:MM y devuelve un objeto time."""
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return None

def _format_time_obj(time_obj):
    """Formatea un objeto time a HH:MM."""
    return time_obj.strftime("%H:%M")

def _split_activity_into_30_min_slots(activity_subject, start_time_obj, end_time_obj, activity_type):
    """
    Divide una actividad que abarca un período de tiempo en franjas de 30 minutos.
    Maneja el descanso de 11:00 a 11:30.
    """
    slots = []
    current_time = datetime.combine(datetime.today(), start_time_obj)
    end_datetime = datetime.combine(datetime.today(), end_time_obj)

    thirty_minutes = timedelta(minutes=30)

    while current_time < end_datetime:
        slot_start_time_obj = current_time.time()
        slot_end_time_obj = (current_time + thirty_minutes).time()

        # Manejo del descanso: si la franja actual comienza antes del descanso y termina durante o después del descanso
        if slot_start_time_obj < BREAK_END_TIME and slot_end_time_obj > BREAK_START_TIME:
            # Si la franja está completamente dentro del descanso (ej. 11:00-11:30), se omite.
            if not (slot_start_time_obj >= BREAK_START_TIME and slot_end_time_obj <= BREAK_END_TIME):
                 # Si la franja cruza el inicio del descanso (ej. 10:30-11:00), se añade.
                if slot_start_time_obj < BREAK_START_TIME: # Esta condición es redundante si la anterior es slot_start_time_obj < BREAK_END_TIME
                    # Esta parte es para franjas que terminan a las 11:00
                    if slot_end_time_obj == BREAK_START_TIME : # Esta franja es 10:30-11:00
                        slot_str = f"{_format_time_obj(slot_start_time_obj)}-{_format_time_obj(slot_end_time_obj)}"
                        if slot_str in VALID_30_MIN_SLOTS_SET:
                           slots.append({'time': slot_str, 'subject': activity_subject, 'type': activity_type})

            # Avanzar current_time al final del descanso si current_time está en el descanso
            if current_time.time() >= BREAK_START_TIME and current_time.time() < BREAK_END_TIME:
                 current_time = datetime.combine(datetime.today(), BREAK_END_TIME)
                 continue # Continuar al siguiente ciclo para generar la franja post-descanso

            # Si la franja comienza justo cuando termina el descanso (11:30)
            # Esta lógica está cubierta por el flujo normal, pero el avance de current_time es clave.

        # Para franjas normales o partes de franjas que no caen en el descanso
        slot_str = f"{_format_time_obj(slot_start_time_obj)}-{_format_time_obj(slot_end_time_obj)}"
        if slot_str in VALID_30_MIN_SLOTS_SET:
            slots.append({'time': slot_str, 'subject': activity_subject, 'type': activity_type})

        current_time += thirty_minutes

    return slots

def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The extracted text from all pages, or None if an error occurs.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF file: {e}")
        return None

    full_text = ""
    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text += page.get_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        doc.close()
        return None

    doc.close()
    return full_text

def extract_tables_from_pdf(pdf_path):
    """
    Extracts all tables from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        list: A list of tables, where each table is a list of lists (rows).
              Returns an empty list if no tables are found or if an error occurs.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF file: {e}")
        return []

    all_tables = []
    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            tables = page.find_tables()
            for table in tables:
                all_tables.append(table.extract())
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
        doc.close()
        return []

    doc.close()
    return all_tables

def process_teacher_schedule_from_page(page_text, page_tables):
    """
    Processes the text and tables from a single PDF page to extract a teacher's schedule.
    NOTE: This function makes many assumptions about the PDF layout.

    Args:
        page_text (str): Full text extracted from the page.
        page_tables (list): List of tables extracted from the page.

    Returns:
        dict: Processed schedule for a teacher, or None if data is insufficient.
    """
    teacher_name = "Unknown Teacher"
    # Attempt to find teacher's name - very basic assumption
    lines = page_text.split('\n')
    if lines:
        # Example: Look for a line starting with "Profesor:"
        for line in lines:
            if line.lower().startswith("profesor:"):
                teacher_name = line.split(":", 1)[1].strip()
                break
        else: # If no "Profesor:" line, take the first non-empty line as a guess
            for line in lines:
                if line.strip():
                    teacher_name = line.strip()
                    break

    schedule = {
        'Lunes': [], 'Martes': [], 'Miércoles': [], 'Jueves': [], 'Viernes': []
    }
    days_of_week_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

    if not page_tables:
        return None # Cannot process schedule without tables

    # Assume the first table is the relevant one for the schedule
    # This is a major assumption and will likely need adjustment
    schedule_table = page_tables[0]

    # Further assumptions:
    # - First row is time slots or headers, actual data starts from second row.
    # - First column is the time slot.
    # - Subsequent columns correspond to Lunes, Martes, ..., Viernes.
    if len(schedule_table) < 2: # Not enough rows for header + data
        return { 'teacher_name': teacher_name, 'schedule': schedule }


    # Try to map columns to days. This is a heuristic.
    # It assumes days are in the header row (first row of the table).
    header_row = [str(cell).lower() if cell else "" for cell in schedule_table[0]]
    day_columns = {} # Maps day name (e.g., "Lunes") to column index

    temp_days_spanish = [day.lower() for day in days_of_week_spanish]

    for col_idx, header_cell_text in enumerate(header_row):
        for day_name_idx, day_name_lower_case in enumerate(temp_days_spanish):
            if day_name_lower_case in header_cell_text:
                day_columns[days_of_week_spanish[day_name_idx]] = col_idx
                break

    # Regex to find time patterns like HH:MM-HH:MM or HH:MM - HH:MM
    time_pattern = re.compile(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})')

    # Assumed first column (index 0) contains the time slots for the rows
    # These are the labels for the rows, not necessarily the times of activities within cells
    row_time_labels_col_idx = 0
    if header_row and not any(day.lower() in header_row[0] for day in days_of_week_spanish):
         # If the first cell of header is not a day, assume it's a time label column
         pass # row_time_labels_col_idx is already 0
    else:
        # This case is tricky: if days start from the very first column,
        # it implies time is not listed as a separate first column.
        # The current logic might struggle here if time isn't explicitly row[0]
        # For now, we'll proceed assuming row[0] might still be useful if it contains time for that row's PRIMARY activity slot.
        pass


    for row_idx in range(1, len(schedule_table)): # Skip header row
        row = schedule_table[row_idx]
        # The time_slot from the first column of the row might not be used if cells define their own times.
        # row_time_slot_label = str(row[row_time_labels_col_idx]) if row and len(row) > row_time_labels_col_idx and row[row_time_labels_col_idx] else None

        for day_name, table_col_idx in day_columns.items():
            if table_col_idx < len(row) and row[table_col_idx]:
                cell_text_original = str(row[table_col_idx])
                cell_text_lower = cell_text_original.lower()

                activity_type = 'clase' # Default
                if "refuerzo" in cell_text_lower or "guardia" in cell_text_lower:
                    activity_type = 'refuerzo'

                # Try to extract time from the cell_text itself
                match = time_pattern.search(cell_text_original)
                subject_text = cell_text_original.strip() # Default subject is full text

                if match:
                    start_time_str, end_time_str = match.groups()
                    start_time_obj = _parse_time_str(start_time_str)
                    end_time_obj = _parse_time_str(end_time_str)

                    # Clean the subject text by removing the time string
                    subject_text = time_pattern.sub('', subject_text).strip()
                    if not subject_text and activity_type == 'refuerzo': # If only time and REFUERZO, make subject REFUERZO
                        subject_text = "REFUERZO" if "refuerzo" in cell_text_lower else "GUARDIA"


                    if start_time_obj and end_time_obj and start_time_obj < end_time_obj:
                        generated_slots = _split_activity_into_30_min_slots(subject_text, start_time_obj, end_time_obj, activity_type)
                        schedule[day_name].extend(generated_slots)
                    else:
                        # Time found but invalid (e.g. end before start, or parse error)
                        # Fallback: add as a single entry using the row's time label if available and sensible
                        # This part is tricky, as the original time_slot variable was removed.
                        # For now, if specific time parsing fails, we log it as a single non-time-specific entry for that day.
                        # A better fallback might be needed.
                        # This assumes the cell_text is the subject for a default slot duration or an unparsed duration.
                        # The original code used 'time_slot' which was the row's first column.
                        # Let's assume for now if specific time parsing fails, we don't add the slot,
                        # as we require explicit timing for 30-min breakdown.
                        # print(f"Warning: Could not parse valid time from '{cell_text_original}' for {teacher_name} on {day_name}. Entry skipped for 30-min breakdown.")
                        pass # Skip if time cannot be parsed from cell for 30-min breakdown

                # else:
                    # No time found in cell_text. This case is problematic for 30-min slot generation.
                    # The original code would have used `time_slot` (from row[0]).
                    # If we need to support activities without explicit times in their cells,
                    # we'd need to infer duration or use the row's time_slot_label and a default duration.
                    # For now, this implementation prioritizes entries with explicit start-end times in the cell.
                    # print(f"Warning: No time information found in cell '{cell_text_original}' for {teacher_name}, {day_name}. Cannot perform 30-min breakdown.")
                    # schedule[day_name].append({
                    #     'time': row_time_slot_label if row_time_slot_label else "Hora Desconocida",
                    #     'subject': subject_text,
                    #     'type': activity_type
                    # })


    # Sort activities within each day by their start time for consistency
    for day_activities in schedule.values():
        day_activities.sort(key=lambda x: x['time'])

    return {
        'teacher_name': teacher_name,
        'schedule': schedule
    }

def parse_schedule_pdf(pdf_path):
    """
    Parses a PDF file to extract teacher schedules from each page.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              a teacher's name and their structured schedule.
              Returns an empty list if an error occurs or no data is found.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF file for schedule parsing: {e}")
        return []

    all_schedules = []
    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text") # Get plain text

            # Extract tables for the current page
            current_page_tables_extracted = []
            tables_on_page = page.find_tables()
            for table_obj in tables_on_page:
                current_page_tables_extracted.append(table_obj.extract())

            if not current_page_tables_extracted and not page_text.strip():
                # Skip page if it's essentially empty (no text, no tables)
                # This might happen for blank pages or pages with only images not OCR'd
                continue

            # Process this page's data
            # Even if there are no tables, page_text might contain the teacher's name
            # The process_teacher_schedule_from_page should handle cases with no tables gracefully
            teacher_data = process_teacher_schedule_from_page(page_text, current_page_tables_extracted)

            if teacher_data: # Only add if some data was processed
                # We might want to add page_num for reference, if multiple teachers share a name
                # teacher_data['page_number'] = page_num
                all_schedules.append(teacher_data)

    except Exception as e:
        print(f"Error processing PDF for schedules: {e}")
        # Optionally, re-raise or handle more gracefully
    finally:
        doc.close()

    return all_schedules


if __name__ == "__main__":
    # This is a placeholder for testing.
    # To test these functions, you would need a sample PDF file.
    # For example:
    # sample_pdf_path = "path/to/your/sample_schedule.pdf"
    # Make sure this PDF exists or the functions will report errors.

    # print(f"Attempting to parse schedule from: {sample_pdf_path}")
    # schedules = parse_schedule_pdf(sample_pdf_path)

    # if schedules:
    #     print(f"\nSuccessfully parsed {len(schedules)} schedule(s):")
    #     for i, schedule_data in enumerate(schedules):
    #         print(f"\n--- Schedule {i+1} ---")
    #         print(f"Teacher: {schedule_data.get('teacher_name', 'N/A')}")
    #         for day, activities in schedule_data.get('schedule', {}).items():
    #             if activities: # Only print days with activities
    #                 print(f"  {day}:")
    #                 for act in activities:
    #                     print(f"    - {act['time']}: {act['subject']} ({act['type']})")
    # else:
    #     print(f"No schedules could be parsed from {sample_pdf_path}, or the PDF was empty/unreadable.")

    # print("\n--- Individual function tests (placeholders) ---")
    # Test text extraction (if you have a PDF and want to see raw text)
    # extracted_text = extract_text_from_pdf(sample_pdf_path)
    # if extracted_text:
    #     print("\nSample Extracted Text (first 500 chars):")
    #     print(extracted_text[:500] + "...")
    # else:
    #     print("Failed to extract text for individual test.")

    # Test table extraction (if you have a PDF and want to see raw tables)
    # extracted_tables = extract_tables_from_pdf(sample_pdf_path)
    # if extracted_tables:
    #     print(f"\nFound {len(extracted_tables)} tables in total (raw extraction):")
    #     # Just print info about the first few tables to avoid too much output
    #     for i, table in enumerate(extracted_tables[:2]):
    #         print(f"  Table {i+1} has {len(table)} rows.")
    # else:
    #     print("No tables found or failed to extract tables for individual test.")

    print("PDF processor module loaded. Add a sample PDF (e.g., 'sample_schedule.pdf' in the root or 'uploads' folder) and uncomment the test blocks to try full parsing and individual extractions.")
