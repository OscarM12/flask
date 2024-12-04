from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import xml.etree.ElementTree as ET
import pymysql
import os
from werkzeug.utils import secure_filename

import os


pymysql.install_as_MySQLdb()

app = Flask(__name__)

# Configuración de la base de datos MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Morenoram12@localhost/archivosXML'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Carpeta de subidas

db = SQLAlchemy(app)

# Modelo para almacenar datos XML
class XMLFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

# Crear la base de datos
with app.app_context():
    db.create_all()

# Ruta principal para listar archivos XML
@app.route('/')
def index():
    files = XMLFile.query.all()
    return render_template('index.html', files=files)

# Ruta para crear un nuevo archivo XML
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['file-name']
        elements = request.form.getlist('elements[]')

        # Crear contenido XML
        root = ET.Element("root")
        for elem in elements:
            try:
                if ':' in elem:
                    tag, text = elem.split(":")
                    child = ET.SubElement(root, tag)
                    child.text = text
                else:
                    print(f"Formato incorrecto para el elemento: {elem}")
            except ValueError:
                print(f"Error procesando el elemento: {elem}")

        xml_content = ET.tostring(root, encoding='unicode')

        # Guardar en la base de datos
        new_file = XMLFile(name=name, content=xml_content)
        db.session.add(new_file)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('create.html')

# Ruta para eliminar archivos XML
@app.route('/delete/<int:id>')
def delete(id):
    file = XMLFile.query.get_or_404(id)
    db.session.delete(file)
    db.session.commit()
    return redirect(url_for('index'))

# Ruta para leer el contenido de un archivo XML
@app.route('/read/<int:id>')
def read(id):
    file = XMLFile.query.get_or_404(id)
    # Mostrar el contenido XML en formato legible
    root = ET.fromstring(file.content)
    xml_dict = {child.tag: child.text for child in root}
    return render_template('read.html', file=file, content=xml_dict)

# Ruta para actualizar un archivo XML
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    file = XMLFile.query.get_or_404(id)

    if request.method == 'POST':
        file.name = request.form['file-name']
        elements = request.form.getlist('elements[]')

        # Crear contenido XML actualizado
        root = ET.Element("root")
        for elem in elements:
            if ':' in elem:
                tag, text = elem.split(":")
                child = ET.SubElement(root, tag)
                child.text = text
        file.content = ET.tostring(root, encoding='unicode')

        db.session.commit()
        return redirect(url_for('index'))

    # Parsear contenido actual para prellenar el formulario
    root = ET.fromstring(file.content)
    elements = [f"{child.tag}:{child.text}" for child in root]
    return render_template('update.html', file=file, elements=elements)

# Ruta para cargar un archivo XML
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index'))
        
    return render_template('upload.html')

# Función para validar archivos permitidos
def allowed_file(filename):
    allowed_extensions = {'xml'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Ruta para convertir texto a XML
@app.route('/convert', methods=['GET', 'POST'])
def convert():
    if request.method == 'POST':
        input_text = request.form['input-text']
        xml_output = convert_text_to_xml(input_text)
        return render_template('convert.html', xml_output=xml_output)
    return render_template('convert.html')

# Función para convertir texto a XML
def convert_text_to_xml(input_text):
    root = ET.Element("root")
    child = ET.SubElement(root, "text")
    child.text = input_text
    return ET.tostring(root, encoding='unicode', method='xml')

if __name__ == '__main__':
    app.run(debug=True)
