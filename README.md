# Programa de Gestión de Sustituciones

Aplicación web para gestionar las sustituciones de profesores en un colegio. Permite cargar horarios desde PDF, solicitar sustituciones y llevar un recuento equilibrado de las mismas.

## Requisitos Previos

*   Python 3.7 o superior
*   Pip (gestor de paquetes de Python)

## Configuración e Inicio

1.  **Clonar el Repositorio (si aplica)**
    Si has obtenido el código como un repositorio git, clónalo:
    ```bash
    git clone <url_del_repositorio>
    cd <nombre_de_la_carpeta_del_repositorio>
    ```

2.  **Crear un Entorno Virtual (Recomendado)**
    Es una buena práctica crear un entorno virtual para aislar las dependencias del proyecto.
    ```bash
    python -m venv venv
    ```
    Activa el entorno virtual:
    *   En Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   En macOS y Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Instalar Dependencias**
    Asegúrate de tener un archivo `requirements.txt` con las dependencias (Flask, PyMuPDF, Pandas). Si no lo tienes, puedes crearlo basándote en las bibliotecas instaladas o instalarlas directamente:
    ```bash
    pip install Flask PyMuPDF pandas
    ```
    (Nota para el desarrollador: Se debería generar un `requirements.txt` si aún no existe).

4.  **Estructura de Carpetas**
    Asegúrate de que la estructura de carpetas sea la correcta. La aplicación espera una carpeta `sustituciones_app` con los archivos Python, y dentro de ella, carpetas `templates`, `uploads` y `data`.
    ```
    .
    ├── sustituciones_app/
    │   ├── app.py
    │   ├── pdf_processor.py
    │   ├── data_manager.py
    │   ├── substitution_logic.py
    │   ├── templates/
    │   ├── static/  (aunque no se use activamente aún)
    │   ├── uploads/ (se crea automáticamente si no existe)
    │   └── data/    (se crea automáticamente si no existe)
    └── README.md
    ```

5.  **Ejecutar la Aplicación**
    Navega hasta el directorio que contiene `app.py` (si estás en la raíz, sería `cd sustituciones_app`) y ejecuta la aplicación Flask:
    ```bash
    cd sustituciones_app
    flask run
    ```
    O también puedes usar:
    ```bash
    python app.py
    ```
    (Esto último funcionará si dentro de `app.py` tienes el bloque `if __name__ == '__main__': app.run(debug=True)`).

6.  **Acceder a la Aplicación**
    Abre tu navegador web y ve a la dirección que se muestra en la terminal (generalmente `http://127.0.0.1:5000/`).

## Uso

1.  **Cargar Horarios**: Ve a la sección "Cargar Horarios" y sube el archivo PDF con los horarios de los profesores.
2.  **Solicitar Sustitución**: Dirígete a "Solicitar Sustitución", selecciona el profesor ausente, el día y la franja horaria.
3.  **Confirmar Sustitución**: Revisa la lista de profesores disponibles (el sistema sugerirá uno para equilibrar) y confirma la asignación.
4.  **Ver Sustituciones**: Consulta el recuento actualizado de sustituciones por profesor.

## Nota sobre los PDFs
La extracción de datos de los PDF es sensible al formato de los mismos. La versión actual asume una estructura de tabla genérica. Si los PDFs tienen un formato muy diferente, el módulo `pdf_processor.py` necesitará ajustes.
