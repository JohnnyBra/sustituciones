# from .data_manager import load_schedules, load_substitution_counts # For standalone testing

# Definición de las franjas horarias válidas (debe ser consistente con app.py)
ALL_DEFINED_30_MIN_SLOTS = [
    '09:00-09:30', '09:30-10:00',
    '10:00-10:30', '10:30-11:00',
    # Descanso 11:00-11:30
    '11:30-12:00', '12:00-12:30',
    '12:30-13:00', '13:00-13:30',
    '13:30-14:00'
]

def _get_time_slots_in_range(start_slot, end_slot, all_defined_slots):
    """
    Genera una lista de franjas horarias de 30 minutos dentro de un rango dado.
    Incluye start_slot y end_slot.
    """
    try:
        start_index = all_defined_slots.index(start_slot)
        end_index = all_defined_slots.index(end_slot)
    except ValueError:
        # Una de las franjas no es válida o no se encuentra
        return []

    if start_index > end_index:
        return [] # Rango inválido

    return all_defined_slots[start_index : end_index + 1]


def find_available_teachers(schedules_data, target_day_of_week, start_hour_slot, end_hour_slot, substitution_counts):
    """
    Encuentra profesores disponibles para un rango de franjas horarias.
    Implementa dos estrategias:
    1. Buscar un profesor para cubrir todo el bloque.
    2. Si no se encuentra, buscar profesores para franjas individuales.

    Args:
        schedules_data (list): Lista de horarios de profesores.
        target_day_of_week (str): El día a verificar.
        start_hour_slot (str): La franja de inicio del rango.
        end_hour_slot (str): La franja de fin del rango.
        substitution_counts (dict): Conteos de sustituciones por profesor.

    Returns:
        dict: Resultados de la búsqueda. Puede ser de tipo 'full_block' o 'individual_slots'.
              Retorna {'type': 'error', 'message': '...'} si el rango es inválido.
    """
    slots_in_range = _get_time_slots_in_range(start_hour_slot, end_hour_slot, ALL_DEFINED_30_MIN_SLOTS)

    if not slots_in_range:
        return {'type': 'error', 'message': 'Rango horario inválido o no se pudieron determinar las franjas.'}

    # Estrategia 1: Buscar un profesor para todo el bloque
    candidates_for_full_block = []
    for teacher_info in schedules_data:
        teacher_name = teacher_info.get('teacher_name')
        schedule = teacher_info.get('schedule')
        if not teacher_name or not schedule:
            continue

        day_schedule = schedule.get(target_day_of_week)
        if not day_schedule:
            continue

        # Convertir el horario del día del profesor en un set de franjas de refuerzo/guardia para búsqueda rápida
        teacher_available_slots_set = set()
        for activity in day_schedule:
            activity_type = activity.get('type', '').lower()
            if activity_type in ['refuerzo', 'guardia']:
                teacher_available_slots_set.add(activity.get('time'))

        # Verificar si el profesor está disponible para TODAS las franjas del rango
        can_cover_full_block = True
        for required_slot in slots_in_range:
            if required_slot not in teacher_available_slots_set:
                can_cover_full_block = False
                break

        if can_cover_full_block:
            candidates_for_full_block.append(teacher_name)

    if candidates_for_full_block:
        # Seleccionar el mejor candidato para el bloque completo
        best_teacher_for_block = select_teacher_for_substitution(candidates_for_full_block, substitution_counts)
        if best_teacher_for_block: # Debería siempre encontrar uno si la lista no está vacía
            return {
                'type': 'full_block',
                'teacher': best_teacher_for_block,
                'slots_covered': slots_in_range,
                'all_candidates_for_block': candidates_for_full_block # Para info adicional en UI si se desea
            }

    # Estrategia 2: (Fallback) Buscar profesores para franjas individuales
    slots_with_candidates_details = []
    any_candidate_found_for_individual = False

    for slot in slots_in_range:
        available_for_this_slot = []
        for teacher_info in schedules_data:
            teacher_name = teacher_info.get('teacher_name')
            schedule = teacher_info.get('schedule')
            if not teacher_name or not schedule:
                continue
            day_schedule = schedule.get(target_day_of_week)
            if not day_schedule:
                continue

            for activity in day_schedule:
                if activity.get('time') == slot and activity.get('type', '').lower() in ['refuerzo', 'guardia']:
                    available_for_this_slot.append(teacher_name)
                    break

        best_candidate_for_slot = None
        if available_for_this_slot:
            any_candidate_found_for_individual = True
            best_candidate_for_slot = select_teacher_for_substitution(available_for_this_slot, substitution_counts)

        slots_with_candidates_details.append({
            'slot': slot,
            'best_candidate': best_candidate_for_slot,
            'all_available_for_slot': available_for_this_slot
        })

    if any_candidate_found_for_individual:
        return {'type': 'individual_slots', 'details': slots_with_candidates_details}
    else:
        # Si ni la estrategia 1 ni la 2 encontraron a nadie para ninguna franja
        return {'type': 'none_available', 'message': 'No se encontraron profesores disponibles para ninguna franja del rango.', 'slots_requested': slots_in_range}


def select_teacher_for_substitution(available_teacher_names, substitution_counts):
    """
    Selects a teacher for substitution based on the minimum number of substitutions.
    This function is now a general helper and can be used by find_available_teachers.

    Args:
        available_teacher_names (list): A list of names of available teachers for a specific slot/block.
        substitution_counts (dict): A dict of teacher names and their substitution counts.

    Returns:
        str: The name of the selected teacher, or None if no teachers are available.
    """
    if not available_teacher_names:
        return None

    min_substitutions = float('inf')
    selected_teacher_name = None

    # Ensure consistent selection if counts are equal by sorting teachers by name
    # This makes testing more predictable.
    for teacher_name in sorted(available_teacher_names):
        count = substitution_counts.get(teacher_name, 0)
        if count < min_substitutions:
            min_substitutions = count
            selected_teacher_name = teacher_name
        # If counts are equal, the first one (due to sorted list) is kept.

    return selected_teacher_name

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

    # Old tests for select_teacher_for_substitution and record_substitution can remain
    # if they are still relevant and use the correct function signatures.
    # Let's assume they are for now, but focus on testing the new find_available_teachers.

    sample_substitution_counts_generic = {
        'Profesor Davila': 2,
        'Profesora Elena': 5,
        'Profesor Carlos': 0, # Explicitly 0
        'Profesora Sofia': 2
    }

    print("\n--- Test: Selecting Teacher for Substitution (Generic Helper) ---")
    teachers1 = ['Profesor Davila', 'Profesora Elena', 'Profesor Carlos', 'Profesora Sofia']
    selected1 = select_teacher_for_substitution(teachers1, sample_substitution_counts_generic)
    print(f"From {teachers1}, selected: {selected1} (Counts: {sample_substitution_counts_generic})")
    assert selected1 == 'Profesor Carlos'

    teachers2 = ['Profesor Davila', 'Profesora Sofia'] # Both count 2
    selected2 = select_teacher_for_substitution(teachers2, sample_substitution_counts_generic)
    print(f"From {teachers2}, selected: {selected2} (Counts: {sample_substitution_counts_generic})")
    assert selected2 == 'Profesor Davila' # Alphabetical tie-break

    print("\n--- Test: Recording Substitution (Generic Helper) ---")
    counts_copy = sample_substitution_counts_generic.copy()
    record_substitution('Profesor Carlos', counts_copy)
    record_substitution('Profesor Carlos', counts_copy)
    record_substitution('Profesora Nueva', counts_copy) # New teacher
    print(f"Updated counts after Carlos x2, Nueva x1: {counts_copy}")
    assert counts_copy['Profesor Carlos'] == 2
    assert counts_copy['Profesora Nueva'] == 1


    # --- New tests for find_available_teachers and _get_time_slots_in_range ---
    new_teacher_name = "Profesora Nueva" # This was from old test, ensure it's not interfering or remove.
    # It's used above in record_substitution test, which is fine.
    counts_for_new = {}
    updated_counts_new_teacher = record_substitution(new_teacher_name, counts_for_new)
    # print(f"Counts for {new_teacher_name} after first substitution: {updated_counts_new_teacher.get(new_teacher_name)}")
    assert updated_counts_new_teacher.get(new_teacher_name) == 1
    updated_counts_new_teacher = record_substitution(new_teacher_name, updated_counts_new_teacher)
    # print(f"Counts for {new_teacher_name} after second substitution: {updated_counts_new_teacher.get(new_teacher_name)}")
    assert updated_counts_new_teacher.get(new_teacher_name) == 2

    print("\n--- Test: _get_time_slots_in_range ---")
    range1 = _get_time_slots_in_range('09:00-09:30', '10:00-10:30', ALL_DEFINED_30_MIN_SLOTS)
    print(f"Range 09:00-09:30 to 10:00-10:30: {range1}")
    assert range1 == ['09:00-09:30', '09:30-10:00', '10:00-10:30']

    range2 = _get_time_slots_in_range('10:30-11:00', '11:30-12:00', ALL_DEFINED_30_MIN_SLOTS)
    print(f"Range 10:30-11:00 to 11:30-12:00 (across break): {range2}")
    assert range2 == ['10:30-11:00', '11:30-12:00'] # Correctly skips 11:00-11:30 as it's not in ALL_DEFINED_30_MIN_SLOTS

    range_empty = _get_time_slots_in_range('10:00-10:30', '09:00-09:30', ALL_DEFINED_30_MIN_SLOTS)
    print(f"Invalid range (end before start): {range_empty}")
    assert range_empty == []

    range_single = _get_time_slots_in_range('12:00-12:30', '12:00-12:30', ALL_DEFINED_30_MIN_SLOTS)
    print(f"Single slot range: {range_single}")
    assert range_single == ['12:00-12:30']

    print("\n--- Test: find_available_teachers (New Logic) ---")
    # Sample data for new tests
    teacher_alpha_schedule = {
        'teacher_name': 'Profesor Alpha', 'schedule': {
            'Lunes': [
                {'time': '09:00-09:30', 'subject': 'GUARDIA', 'type': 'refuerzo'},
                {'time': '09:30-10:00', 'subject': 'GUARDIA', 'type': 'refuerzo'},
                {'time': '10:00-10:30', 'subject': 'Matematicas', 'type': 'clase'},
            ]
        }
    }
    teacher_beta_schedule = {
        'teacher_name': 'Profesora Beta', 'schedule': {
            'Lunes': [
                {'time': '09:00-09:30', 'subject': 'GUARDIA', 'type': 'refuerzo'},
                {'time': '09:30-10:00', 'subject': 'GUARDIA', 'type': 'refuerzo'},
                {'time': '10:00-10:30', 'subject': 'GUARDIA', 'type': 'refuerzo'}, # Beta can cover full block
            ]
        }
    }
    teacher_gamma_schedule = {
        'teacher_name': 'Profesor Gamma', 'schedule': {
            'Lunes': [
                {'time': '10:00-10:30', 'subject': 'REFUERZO', 'type': 'refuerzo'},
            ]
        }
    }
    test_schedules = [teacher_alpha_schedule, teacher_beta_schedule, teacher_gamma_schedule]
    test_counts = {'Profesor Alpha': 1, 'Profesora Beta': 2, 'Profesor Gamma': 0}

    # Test Case 1: Full block covered by Beta
    print("\nTest Case 1: Full block (09:00-10:30 Lunes)")
    result1 = find_available_teachers(test_schedules, 'Lunes', '09:00-09:30', '10:00-10:30', test_counts)
    print(f"Result: {result1}")
    assert result1['type'] == 'full_block'
    assert result1['teacher'] == 'Profesora Beta' # Beta has more subs but is the only one for full block
    assert len(result1['slots_covered']) == 3

    # Test Case 2: Individual slots (Alpha and Gamma, Beta also)
    # Change Beta's schedule so she cannot cover the full block '09:00-09:30' to '09:30-10:00'
    teacher_beta_schedule_modified = {
        'teacher_name': 'Profesora Beta', 'schedule': {
            'Lunes': [
                {'time': '09:00-09:30', 'subject': 'Clase', 'type': 'clase'}, # No longer refuerzo
                {'time': '09:30-10:00', 'subject': 'GUARDIA', 'type': 'refuerzo'},
            ]
        }
    }
    test_schedules_indiv = [teacher_alpha_schedule, teacher_beta_schedule_modified, teacher_gamma_schedule]
    print("\nTest Case 2: Full block covered by Alpha after Beta modified (09:00-09:30 to 09:30-10:00 Lunes)")
    result2 = find_available_teachers(test_schedules_indiv, 'Lunes', '09:00-09:30', '09:30-10:00', test_counts)
    print(f"Result: {result2}")
    assert result2['type'] == 'full_block'
    assert result2['teacher'] == 'Profesor Alpha'
    assert len(result2['slots_covered']) == 2

    # Test Case 2b: Specifically for individual_slots
    # Alpha: 09:00-09:30 (refuerzo), 09:30-10:00 (refuerzo)
    # Beta_mod: 09:30-10:00 (refuerzo)
    # Gamma: 10:00-10:30 (refuerzo)
    # Request: 09:00-09:30 to 10:00-10:30
    # Expected: Alpha for 09:00-09:30, Alpha for 09:30-10:00, Gamma for 10:00-10:30
    # No one covers the full block of three slots.
    teacher_alpha_case2b = {
        'teacher_name': 'Profesor Alpha', 'schedule': { # Counts: Alpha 1
            'Lunes': [
                {'time': '09:00-09:30', 'subject': 'GUARDIA', 'type': 'refuerzo'},
                {'time': '09:30-10:00', 'subject': 'GUARDIA', 'type': 'refuerzo'},
            ]
        }
    }
    teacher_beta_case2b = { # Counts: Beta 2
        'teacher_name': 'Profesora Beta', 'schedule': {
            'Lunes': [
                 # Beta no disponible en la primera franja
                {'time': '09:30-10:00', 'subject': 'GUARDIA', 'type': 'refuerzo'},
                {'time': '10:00-10:30', 'subject': 'GUARDIA', 'type': 'refuerzo'},
            ]
        }
    }
    teacher_gamma_case2b = { # Counts: Gamma 0
         'teacher_name': 'Profesor Gamma', 'schedule': {
            'Lunes': [
                {'time': '10:00-10:30', 'subject': 'REFUERZO', 'type': 'refuerzo'},
            ]
        }
    }
    test_schedules_case2b = [teacher_alpha_case2b, teacher_beta_case2b, teacher_gamma_case2b]
    test_counts_case2b = {'Profesor Alpha': 1, 'Profesora Beta': 2, 'Profesor Gamma': 0}

    print("\nTest Case 2b: Individual slots (09:00-09:30 to 10:00-10:30 Lunes)")
    result2b = find_available_teachers(test_schedules_case2b, 'Lunes', '09:00-09:30', '10:00-10:30', test_counts_case2b)
    print(f"Result for 2b: {result2b}")
    assert result2b['type'] == 'individual_slots'
    assert len(result2b['details']) == 3
    assert result2b['details'][0]['slot'] == '09:00-09:30'
    assert result2b['details'][0]['best_candidate'] == 'Profesor Alpha'
    assert result2b['details'][1]['slot'] == '09:30-10:00'
    assert result2b['details'][1]['best_candidate'] == 'Profesor Alpha' # Alpha (1) vs Beta (2)
    assert result2b['details'][2]['slot'] == '10:00-10:30'
    assert result2b['details'][2]['best_candidate'] == 'Profesor Gamma' # Gamma (0) vs Beta (2)

    # Test Case 3: No one available for any slot in range
    print("\nTest Case 3: No one available (11:30-12:00 to 12:00-12:30 Lunes)")
    result3 = find_available_teachers(test_schedules, 'Lunes', '11:30-12:00', '12:00-12:30', test_counts)
    print(f"Result: {result3}")
    assert result3['type'] == 'none_available'
    assert len(result3['slots_requested']) == 2

    # Test Case 4: Invalid range
    print("\nTest Case 4: Invalid Range")
    result4 = find_available_teachers(test_schedules, 'Lunes', '10:00-10:30', '09:00-09:30', test_counts)
    print(f"Result: {result4}")
    assert result4['type'] == 'error'

    # Test Case 5: One slot, multiple available, select best
    teacher_delta_schedule = {
        'teacher_name': 'Profesor Delta', 'schedule': {
            'Lunes': [ {'time': '09:00-09:30', 'subject': 'GUARDIA', 'type': 'refuerzo'}, ]
        }
    }
    test_schedules_single_slot = [teacher_alpha_schedule, teacher_beta_schedule, teacher_gamma_schedule, teacher_delta_schedule]
    test_counts_single_slot = {'Profesor Alpha': 1, 'Profesora Beta': 2, 'Profesor Gamma': 3, 'Profesor Delta': 0} # Delta is best
    print("\nTest Case 5: Single slot (09:00-09:30), multiple available")
    # For a single slot, it should still prefer 'full_block' type if someone can cover it.
    result5 = find_available_teachers(test_schedules_single_slot, 'Lunes', '09:00-09:30', '09:00-09:30', test_counts_single_slot)
    print(f"Result: {result5}")
    assert result5['type'] == 'full_block' # Because it's a "block" of one slot
    assert result5['teacher'] == 'Profesor Delta'
    assert result5['slots_covered'] == ['09:00-09:30']

    print("\nSubstitution logic tests completed.")
