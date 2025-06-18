import fitz  # PyMuPDF

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
    day_columns = {}

    temp_days_spanish = [day.lower() for day in days_of_week_spanish]

    for i, header_cell in enumerate(header_row):
        for day_idx, day_name_lower in enumerate(temp_days_spanish):
            if day_name_lower in header_cell: # Check if "lunes" is in "lunes\n01/01"
                day_columns[days_of_week_spanish[day_idx]] = i
                break # Found day for this column

    # If we couldn't map days from header, assume fixed order: Col 1 = Lunes, Col 2 = Martes ...
    if not day_columns or len(day_columns) < len(days_of_week_spanish):
        # Fallback or more robust day detection needed here
        # For now, let's assume fixed column order if detection fails for all days
        # This is a weak assumption.
        if len(header_row) > len(days_of_week_spanish): # Time column + 5 days
             day_columns = {day: i+1 for i, day in enumerate(days_of_week_spanish)}


    for row_idx in range(1, len(schedule_table)): # Skip header row
        row = schedule_table[row_idx]
        time_slot = str(row[0]) if row and row[0] else "Unknown Time"

        for day_name, col_idx in day_columns.items():
            if col_idx < len(row) and row[col_idx]:
                cell_text = str(row[col_idx])
                activity_type = 'clase' # Default
                if "refuerzo" in cell_text.lower() or "guardia" in cell_text.lower():
                    activity_type = 'refuerzo'

                schedule[day_name].append({
                    'time': time_slot,
                    'subject': cell_text.strip(), # Clean up whitespace
                    'type': activity_type
                })

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
