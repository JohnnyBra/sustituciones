import os
import datetime # Added import
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

from .pdf_processor import parse_schedule_pdf
from .data_manager import save_schedules, load_schedules, load_substitution_counts
from .substitution_logic import find_available_teachers, select_teacher_for_substitution, record_substitution

app = Flask(__name__)
app.secret_key = 'os_is_usually_good_enough_for_dev_but_change_this_for_prod' # Replace in production
UPLOAD_FOLDER = 'sustituciones_app/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
FRANJAS_HORARIAS = ["08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", "13:00-14:00", "14:00-15:00"] # Extended example

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
    if request.method == 'POST':
        profesor_ausente = request.form.get('profesor_ausente')
        dia_semana = request.form.get('dia_semana')
        franja_horaria = request.form.get('franja_horaria')

        if not all([profesor_ausente, dia_semana, franja_horaria]):
            flash('Todos los campos son requeridos.', 'error')
            return redirect(url_for('solicitar_sustitucion_route'))

        # Store in session for more robustness if many parameters or sensitive data
        # session['substitution_request'] = {
        #     'profesor_ausente': profesor_ausente,
        #     'dia_semana': dia_semana,
        #     'franja_horaria': franja_horaria
        # }
        # return redirect(url_for('confirmar_sustitucion_route'))

        # Using query parameters for simplicity as requested
        return redirect(url_for('confirmar_sustitucion_route',
                                profesor_ausente=profesor_ausente,
                                dia_semana=dia_semana,
                                franja_horaria=franja_horaria))

    # GET request
    schedules = load_schedules()
    if not schedules:
        flash("No hay horarios cargados. Por favor, carga primero un archivo de horarios.", "warning")
        # return redirect(url_for('cargar_horarios_route')) # Or render with a message

    teacher_names = sorted(list(set(s.get('teacher_name', 'Nombre Desconocido') for s in schedules if s.get('teacher_name'))))

    return render_template('solicitar_sustitucion.html',
                           profesores=teacher_names,
                           dias_semana=DIAS_SEMANA,
                           franjas_horarias=FRANJAS_HORARIAS)

from .data_manager import save_schedules, load_schedules, load_substitution_counts, save_substitution_counts

@app.route('/confirmar_sustitucion', methods=['GET', 'POST'])
def confirmar_sustitucion_route():
    if request.method == 'POST':
        profesor_ausente_original = request.form.get('profesor_ausente_original')
        dia_original = request.form.get('dia_original')
        hora_original = request.form.get('hora_original')
        profesor_seleccionado = request.form.get('profesor_seleccionado')

        if not profesor_seleccionado:
            flash("Debes seleccionar un profesor para realizar la sustitución.", "error")
            # Need to repopulate GET context if redirecting back to confirm page
            return redirect(url_for('confirmar_sustitucion_route',
                                    profesor_ausente=profesor_ausente_original,
                                    dia_semana=dia_original,
                                    franja_horaria=hora_original))

        current_counts = load_substitution_counts()
        updated_counts = record_substitution(profesor_seleccionado, current_counts)
        save_substitution_counts(updated_counts)

        flash(f"Sustitución asignada a '{profesor_seleccionado}' para el {dia_original} de {hora_original} (ausencia de {profesor_ausente_original}).", "success")
        return redirect(url_for('solicitar_sustitucion_route')) # Or a new page like 'ver_sustituciones'

    # GET request
    profesor_ausente = request.args.get('profesor_ausente')
    dia_semana = request.args.get('dia_semana')
    franja_horaria = request.args.get('franja_horaria')

    if not all([profesor_ausente, dia_semana, franja_horaria]):
        flash("Faltan datos para confirmar la sustitución (profesor ausente, día o franja). Por favor, inténtalo de nuevo desde 'Solicitar Sustitución'.", "error")
        return redirect(url_for('solicitar_sustitucion_route'))

    schedules_data = load_schedules()
    if not schedules_data:
        flash("No hay datos de horarios cargados. No se puede determinar disponibilidad.", "error")
        return redirect(url_for('solicitar_sustitucion_route'))

    substitution_counts = load_substitution_counts()

    all_available_teachers = find_available_teachers(schedules_data, dia_semana, franja_horaria)

    # Exclude the absent teacher from the list of available teachers
    # Also, create a list of dicts with name and current count for the template
    truly_available_teachers_with_counts = []
    for teacher_name in all_available_teachers:
        if teacher_name != profesor_ausente:
            truly_available_teachers_with_counts.append({
                "name": teacher_name,
                "count": substitution_counts.get(teacher_name, 0)
            })

    # Get a suggested teacher to pre-select in the form
    # Need to pass only names to select_teacher_for_substitution
    names_of_truly_available = [t['name'] for t in truly_available_teachers_with_counts]
    suggested_teacher = select_teacher_for_substitution(names_of_truly_available, substitution_counts)

    return render_template('confirmar_sustitucion.html',
                           profesor_ausente=profesor_ausente,
                           dia_semana=dia_semana,
                           franja_horaria=franja_horaria,
                           available_teachers_with_counts=truly_available_teachers_with_counts,
                           suggested_teacher=suggested_teacher,
                           substitution_counts=substitution_counts # Pass all counts for display if needed
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
