# Teacher Substitution Management System

## Description
This program helps manage teacher substitutions by parsing schedules from PDF files. It identifies teachers available for substitution (those with "reinforcement" or "guardia" hours) and suggests a substitute based on a balanced count of prior substitutions.

## Features
- Parses teacher schedules from PDF files.
- Identifies reinforcement/guardia hours for substitution availability.
- Allows recording of teacher absences for specific time slots.
- Suggests the most suitable substitute based on availability and a balanced distribution of substitution duties.
- Allows manual selection of a substitute from the list of available teachers.
- Tracks and displays substitution counts per teacher.
- Provides a command-line interface (CLI) for all interactions.

## Setup and Installation
- **Python:** Python 3.8+ is recommended.
- **Dependencies:**
    - The primary dependency is `pdfplumber` for parsing PDF files.
    - Install it using pip:
      ```bash
      pip install pdfplumber
      ```
    - (Note: If a `requirements.txt` file were provided, you could use `pip install -r requirements.txt`)

## How to Run
1.  Navigate to the root directory of the project in your terminal.
2.  Execute the main application script:
    ```bash
    python src/main.py
    ```
3.  The program will then prompt you to enter the path to the teacher schedule PDF file.

## PDF Schedule Format Assumptions
The `src/pdf_parser.py` module makes several critical assumptions about the format of the input PDF schedule. If your PDF differs significantly, the parser may not work correctly.

-   **One Teacher Per Page:** Each page in the PDF is assumed to represent the schedule for a single teacher.
-   **Teacher Name Location:** The teacher's name is assumed to be the first significant block of text found on the page *before* any tables.
    -   If no text is found in the expected area, or if parsing the name is problematic, a placeholder like "Unknown Teacher - Page X" will be used.
-   **Schedule Table:** The first table extracted from each page is assumed to be the teacher's weekly schedule.
-   **Table Structure:**
    -   The **first row** of the table is treated as a header row and is skipped during parsing.
    -   **Column 0 (First Column):** Contains the time slot for the row, formatted as "HH:MM-HH:MM" (e.g., "08:00-09:00").
    -   **Columns 1 through 5:** These columns are assumed to represent Monday, Tuesday, Wednesday, Thursday, and Friday, respectively.
-   **Activity Description:** The content of each cell within the day columns (Monday-Friday) is taken as the name or description of the scheduled activity.
-   **Identifying Reinforcement Hours:** Activities are marked as 'reinforcement' (and thus available for substitution duties) if their description text contains the keywords "REFUERZO" or "GUARDIA" (case-insensitive). All other non-empty slots are typically considered 'class' type activities.

## Modules Overview
The project is structured into several Python modules within the `src` directory:

-   **`src/data_models.py`:** Defines the core data structures used throughout the application, such as `TimeSlot`, `ScheduledActivity`, `TeacherSchedule`, and `SubstitutionLog`.
-   **`src/pdf_parser.py`:** Contains the logic for opening and parsing teacher schedule data from PDF files, based on the assumptions listed above.
-   **`src/schedule_manager.py`:** Manages the collection of loaded teacher schedules. It provides functionalities to retrieve specific schedules and find teachers who are available during a given time slot.
-   **`src/substitution_handler.py`:** Implements the logic for selecting a substitute teacher from a list of available candidates. It aims to balance the workload by tracking how many times each teacher has been assigned a substitution.
-   **`src/main.py`:** The main entry point of the application. It provides the command-line interface (CLI) for users to interact with the system (load schedules, record absences, view counts, etc.).
-   **`tests/`:** This directory contains unit tests for the various modules to ensure they function correctly.

## How to Run Unit Tests
To run the automated unit tests:

1.  Ensure you are in the root directory of the project.
2.  Execute the following command in your terminal:
    ```bash
    python -m unittest discover tests
    ```
    This will automatically discover and run all tests defined in the `tests` directory.
