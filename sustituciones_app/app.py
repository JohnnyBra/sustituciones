import os
import datetime # Added import
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

from .pdf_processor import parse_schedule_pdf
from .data_manager import (
    save_schedules,
    load_schedules,
    load_substitution_counts,
    save_substitution_counts,
    append_to_substitution_history # Added import
)
from .substitution_logic import (
    find_available_teachers,
    select_teacher_for_substitution,
    record_substitution,
    _get_time_slots_in_range,
    ALL_DEFINED_30_MIN_SLOTS
)

app = Flask(__name__)
app.secret_key = 'os_is_usually_good_enough_for_dev_but_change_this_for_prod' # Replace in production
UPLOAD_FOLDER = 'sustituciones_app/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
FRANJAS_HORARIAS_30_MIN = [
    '09:00-09:30', '09:30-10:00',
    '10:00-10:30', '10:30-11:00',
    # Descanso 11:00-11:30
    '11:30-12:00', '12:00-12:30',
    '12:30-13:00', '13:00-13:30',
    '13:30-14:00'
]
# Mantener FRANJAS_HORARIAS original si aún se usa en algún lugar, o decidir si se reemplaza completamente.
# Por ahora, la tarea pide que la nueva constante sea usada en `solicitar_sustitucion_route`.
# Si FRANJAS_HORARIAS ya no se usa, se podría eliminar.
# Para este paso, me centraré en usar FRANJAS_HORARIAS_30_MIN donde se indique.

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index_route():
    return render_template('index.html')

@app.route('/cargar_horarios', methods=['GET', 'POST'])
def cargar_horarios_route():
    if request.method == 'POST':
        if 'schedule_pdf' not in request.files:
            flash('No se encontró el campo del archivo en la solicitud.', 'error')
            return redirect(request.url)

        file = request.files['schedule_pdf']

        if file.filename == '':
            flash('Ningún archivo seleccionado.', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                file.save(pdf_path)
                flash(f"Archivo '{filename}' subido correctamente. Procesando...", 'success')

                schedules_data = parse_schedule_pdf(pdf_path)

                if not schedules_data:
                    flash(f"No se pudo extraer ningún horario del PDF '{filename}'. Verifique el formato del archivo o que no esté vacío/corrupto.", 'error')
                    return redirect(request.url)

                save_schedules(schedules_data)
                flash(f"Horarios procesados y guardados correctamente desde '{filename}'. Se encontraron {len(schedules_data)} horarios.", 'success')

                return redirect(url_for('cargar_horarios_route'))

            except Exception as e:
                flash(f"Ocurrió un error al procesar el archivo '{filename}': {e}", 'error')
                return redirect(request.url)
        else:
            flash('Tipo de archivo no permitido. Por favor, sube un archivo PDF.', 'error')
            return redirect(request.url)

    return render_template('cargar_horarios.html')

@app.route('/solicitar_sustitucion', methods=['GET', 'POST'])
def solicitar_sustitucion_route():
    # Ensure datetime is imported (it was already imported as `import datetime` at the top)
    # from datetime import datetime # This specific form is not needed if `datetime.datetime` is used.

    if request.method == 'POST':
        profesor_ausente = request.form.get('profesor_ausente')
        dia_semana = request.form.get('dia_semana')
        fecha_sustitucion_str = request.form.get('fecha_sustitucion')
        dia_completo = request.form.get('dia_completo') == 'on'

        desde_hora_val = request.form.get('desde_hora')
        hasta_hora_val = request.form.get('hasta_hora')

        # Validaciones
        if not profesor_ausente or not dia_semana:
            flash('Profesor ausente y día de la semana son campos requeridos.', 'error')
            # Need to re-pass data for GET render
            return _render_solicitar_sustitucion_form()

        if not fecha_sustitucion_str:
            flash('Por favor, selecciona una fecha para la sustitución.', 'error')
            return _render_solicitar_sustitucion_form()
        try:
            fecha_obj = datetime.datetime.strptime(fecha_sustitucion_str, '%Y-%m-%d').date()
            if fecha_obj < datetime.date.today():
                flash('No puedes seleccionar una fecha pasada para la sustitución.', 'error')
                return _render_solicitar_sustitucion_form()
        except ValueError:
            flash('Formato de fecha inválido. Por favor, usa el selector de fecha.', 'error')
            return _render_solicitar_sustitucion_form()

        final_desde_hora = ""
        final_hasta_hora = ""

        if dia_completo:
            if FRANJAS_HORARIAS_30_MIN:
                final_desde_hora = FRANJAS_HORARIAS_30_MIN[0]
                final_hasta_hora = FRANJAS_HORARIAS_30_MIN[-1]
            else:
                flash('No hay franjas horarias definidas para seleccionar "Día Completo".', 'error')
                return redirect(url_for('solicitar_sustitucion_route'))
        else:
            if not desde_hora_val or not hasta_hora_val:
                flash('Debes seleccionar "Desde Hora" y "Hasta Hora" si no marcas "Día Completo".', 'error')
                return redirect(url_for('solicitar_sustitucion_route'))

            # Validar que hasta_hora es posterior a desde_hora
            try:
                idx_desde = FRANJAS_HORARIAS_30_MIN.index(desde_hora_val)
                idx_hasta = FRANJAS_HORARIAS_30_MIN.index(hasta_hora_val)
                if idx_hasta < idx_desde:
                    flash('"Hasta Hora" debe ser posterior o igual a "Desde Hora".', 'error')
                    return _render_solicitar_sustitucion_form()
            except ValueError:
                flash('Valores de franja horaria no válidos.', 'error')
                return _render_solicitar_sustitucion_form()

            final_desde_hora = desde_hora_val
            final_hasta_hora = hasta_hora_val

        return redirect(url_for('confirmar_sustitucion_route',
                                profesor_ausente=profesor_ausente,
                                dia_semana=dia_semana,
                                rango_desde_hora=final_desde_hora,
                                rango_hasta_hora=final_hasta_hora,
                                fecha_sustitucion=fecha_sustitucion_str
                                ))

    # GET request
    return _render_solicitar_sustitucion_form()

def _render_solicitar_sustitucion_form():
    """Helper para renderizar el formulario de solicitud, usado en GET y en POST con errores."""
    schedules = load_schedules()
    # No es necesario flashear aquí si los horarios no están cargados,
    # la plantilla ya tiene una condición para mostrar un mensaje.
    # if not schedules:
    #     flash("No hay horarios cargados. Por favor, carga primero un archivo de horarios.", "warning")

    teacher_names = sorted(list(set(s.get('teacher_name', 'Nombre Desconocido') for s in schedules if s.get('teacher_name'))))
    today_date_str = datetime.date.today().strftime('%Y-%m-%d')

    return render_template('solicitar_sustitucion.html',
                           profesores=teacher_names,
                           dias_semana=DIAS_SEMANA,
                           franjas_horarias=FRANJAS_HORARIAS_30_MIN,
                           today_date=today_date_str)


@app.route('/confirmar_sustitucion', methods=['GET', 'POST'])
def confirmar_sustitucion_route():
    if request.method == 'POST':
        profesor_ausente_original = request.form.get('profesor_ausente_original')
        dia_original = request.form.get('dia_original')
        fecha_sustitucion = request.form.get('fecha_sustitucion') # Get the date
        confirmation_type = request.form.get('confirmation_type')

        current_counts = load_substitution_counts()

        slots_actually_assigned_count = 0
        # Store details for flash message and history grouped by substituting teacher
        assignments_by_teacher = {} # teacher_name: {'slots': [slot1, slot2], 'total_slots_for_teacher': count}

        if confirmation_type == 'full_block':
            profesor_seleccionado = request.form.get('profesor_seleccionado_full_block')
            rango_desde_original = request.form.get('rango_desde_original_hidden')
            rango_hasta_original = request.form.get('rango_hasta_original_hidden')
            slots_covered = _get_time_slots_in_range(rango_desde_original, rango_hasta_original, ALL_DEFINED_30_MIN_SLOTS)

            if profesor_seleccionado and slots_covered:
                for _ in slots_covered: # Call record_substitution for each 30-min slot
                    current_counts = record_substitution(profesor_seleccionado, current_counts)
                slots_actually_assigned_count += len(slots_covered)

                assignments_by_teacher[profesor_seleccionado] = {
                    'slots': slots_covered,
                    'total_slots_for_teacher': len(slots_covered)
                }

        elif confirmation_type == 'individual_slots':
            rango_desde_original = request.form.get('rango_desde_original_hidden')
            rango_hasta_original = request.form.get('rango_hasta_original_hidden')
            slots_in_original_range = _get_time_slots_in_range(rango_desde_original, rango_hasta_original, ALL_DEFINED_30_MIN_SLOTS)

            temp_assignments_for_teacher = {} # Used to group slots for a teacher before adding to assignments_by_teacher

            for slot in slots_in_original_range:
                profesor_asignado_para_slot = request.form.get(f'assign_{slot}')
                if profesor_asignado_para_slot and profesor_asignado_para_slot != "NO_ASIGNAR":
                    current_counts = record_substitution(profesor_asignado_para_slot, current_counts) # Called per slot
                    slots_actually_assigned_count += 1

                    if profesor_asignado_para_slot not in temp_assignments_for_teacher:
                        temp_assignments_for_teacher[profesor_asignado_para_slot] = []
                    temp_assignments_for_teacher[profesor_asignado_para_slot].append(slot)

            for teacher, slots in temp_assignments_for_teacher.items():
                assignments_by_teacher[teacher] = {
                    'slots': sorted(slots), # Sort slots for consistent history
                    'total_slots_for_teacher': len(slots)
                }

        if slots_actually_assigned_count > 0:
            save_substitution_counts(current_counts)

            # Create history records
            for teacher_substituto, assignment_details in assignments_by_teacher.items():
                history_record = {
                    "timestamp": datetime.datetime.now().isoformat(), # Add a timestamp
                    "profesor_sustituto": teacher_substituto,
                    "profesor_ausente": profesor_ausente_original,
                    "fecha_sustitucion": fecha_sustitucion,
                    "dia_semana": dia_original,
                    "slots_cubiertos_detalle": assignment_details['slots'],
                    "numero_slots": assignment_details['total_slots_for_teacher']
                }
                append_to_substitution_history(history_record)

            flash_message = f"Sustitución(es) asignada(s) para {profesor_ausente_original} el {dia_original} ({fecha_sustitucion}):<br>"
            for teacher, details in assignments_by_teacher.items():
                flash_message += f"- {teacher} cubrirá: {', '.join(details['slots'])} ({details['total_slots_for_teacher']} franja(s)).<br>"
            flash(flash_message, "success")
        else:
            flash("No se asignó ninguna sustitución.", "info")

        return redirect(url_for('solicitar_sustitucion_route'))

    # --- GET request ---
    profesor_ausente = request.args.get('profesor_ausente')
    dia_semana = request.args.get('dia_semana')
    rango_desde_hora = request.args.get('rango_desde_hora')
    rango_hasta_hora = request.args.get('rango_hasta_hora')
    fecha_sustitucion = request.args.get('fecha_sustitucion') # Get the date

    if not all([profesor_ausente, dia_semana, rango_desde_hora, rango_hasta_hora, fecha_sustitucion]):
        flash("Faltan datos para confirmar la sustitución (profesor, día, rango horario o fecha). Por favor, inténtalo de nuevo.", "error")
        return redirect(url_for('solicitar_sustitucion_route'))

    schedules_data = load_schedules()
    if not schedules_data:
        flash("No hay datos de horarios cargados. No se puede determinar disponibilidad.", "error")
        return redirect(url_for('solicitar_sustitucion_route'))

    substitution_counts = load_substitution_counts()

    # Llamar a la nueva función find_available_teachers
    # Le pasamos substitution_counts para que pueda usarlo internamente si es necesario
    resultado_busqueda = find_available_teachers(
        schedules_data, dia_semana, rango_desde_hora, rango_hasta_hora, substitution_counts
    )

    # Determinar si se necesita personal externo
    necesita_externo = False
    slots_in_request_range = _get_time_slots_in_range(rango_desde_hora, rango_hasta_hora, ALL_DEFINED_30_MIN_SLOTS)

    if resultado_busqueda['type'] == 'none_available':
        necesita_externo = True
    elif resultado_busqueda['type'] == 'individual_slots':
        # Verificar si cada slot del rango original tiene un 'best_candidate'
        covered_slots_in_individual_mode = set()
        for detail in resultado_busqueda.get('details', []):
            if detail.get('best_candidate'):
                covered_slots_in_individual_mode.add(detail['slot'])

        for slot in slots_in_request_range:
            if slot not in covered_slots_in_individual_mode:
                necesita_externo = True
                break
    elif resultado_busqueda['type'] == 'error':
         flash(f"Error en la búsqueda: {resultado_busqueda.get('message', 'Error desconocido.')}", "error")
         return redirect(url_for('solicitar_sustitucion_route'))


    return render_template('confirmar_sustitucion.html',
                           profesor_ausente=profesor_ausente,
                           dia_semana=dia_semana,
                           rango_desde_hora=rango_desde_hora,
                           rango_hasta_hora=rango_hasta_hora,
                           fecha_sustitucion=fecha_sustitucion, # Pass to template
                           resultado_busqueda=resultado_busqueda,
                           substitution_counts=substitution_counts,
                           necesita_externo=necesita_externo,
                           slots_in_request_range=slots_in_request_range
                           )

@app.route('/ver_sustituciones', methods=['GET'])
def ver_sustituciones_route():
    substitution_counts = load_substitution_counts()
    # Sort by count descending, then by name ascending for tie-breaking
    sorted_counts = sorted(substitution_counts.items(), key=lambda item: (-item[1], item[0]))
    return render_template('ver_sustituciones.html', counts=sorted_counts)

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.date.today().year}

if __name__ == '__main__':
    print("Flask app 'app.py' is ready to be run. Use 'flask run' or 'python -m flask run'.")
    print("Ensure you are in the directory containing 'sustituciones_app' or set FLASK_APP appropriately.")
    print("Example: export FLASK_APP=sustituciones_app.app")
    print("Then: flask run --host=0.0.0.0")
