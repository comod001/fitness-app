import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

database_url = os.environ.get('DATABASE_URL', 'sqlite:///fitness.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
db = SQLAlchemy(app)

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    series = db.Column(db.String(50), nullable=False)
    completado = db.Column(db.Boolean, default=False)
    dia = db.Column(db.String(50), nullable=False, default='Viernes')
    nota = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "series": self.series,
            "completado": self.completado,
            "dia": self.dia,
            "nota": self.nota or "",
        }

with app.app_context():
    db.create_all()
    if Ejercicio.query.count() == 0:
        ejercicios = [
            # Viernes
            Ejercicio(dia="Viernes", nombre="Jalón al pecho", series="4x10"),
            Ejercicio(dia="Viernes", nombre="Remo en máquina", series="3x12"),
            Ejercicio(dia="Viernes", nombre="Remo con mancuerna un brazo", series="3x12"),
            Ejercicio(dia="Viernes", nombre="Pullover en polea", series="3x15"),
            Ejercicio(dia="Viernes", nombre="Curl con barra", series="3x12"),
            Ejercicio(dia="Viernes", nombre="Curl martillo", series="3x12"),
            Ejercicio(dia="Viernes", nombre="Cardio", series="15 min"),
            # Sábado
            Ejercicio(dia="Sábado", nombre="Sentadilla hack squat", series="4x10"),
            Ejercicio(dia="Sábado", nombre="Prensa de piernas", series="4x12"),
            Ejercicio(dia="Sábado", nombre="Extensión de cuádriceps", series="3x15"),
            Ejercicio(dia="Sábado", nombre="Hip thrust", series="4x12"),
            Ejercicio(dia="Sábado", nombre="Peso muerto rumano", series="3x12"),
            Ejercicio(dia="Sábado", nombre="Cardio caminadora inclinada", series="20 min"),
            # Domingo
            Ejercicio(dia="Domingo", nombre="Press en máquina", series="4x10"),
            Ejercicio(dia="Domingo", nombre="Aperturas en polea", series="3x15"),
            Ejercicio(dia="Domingo", nombre="Press militar mancuernas", series="4x10"),
            Ejercicio(dia="Domingo", nombre="Elevaciones laterales", series="4x15"),
            Ejercicio(dia="Domingo", nombre="Extensión tríceps en polea", series="3x15"),
            Ejercicio(dia="Domingo", nombre="Fondos en banco", series="3x12"),
            Ejercicio(dia="Domingo", nombre="Cardio", series="15 min"),
        ]
        db.session.add_all(ejercicios)
        db.session.commit()

# API endpoints
@app.route('/api/rutina')
def get_rutina():
    rutina = Ejercicio.query.all()
    return jsonify([e.to_dict() for e in rutina])

@app.route('/api/marcar/<int:id>', methods=['POST'])
def marcar(id):
    ejercicio = Ejercicio.query.get(id)
    ejercicio.completado = not ejercicio.completado
    db.session.commit()
    return jsonify(ejercicio.to_dict())

# Panel admin
@app.route('/admin')
def admin():
    dias = ["Viernes", "Sábado", "Domingo"]
    rutina = {dia: Ejercicio.query.filter_by(dia=dia).all() for dia in dias}
    return render_template('admin.html', rutina=rutina, dias=dias)

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form['nombre']
    series = request.form['series']
    dia = request.form['dia']
    nota = request.form.get('nota', '')
    nuevo = Ejercicio(nombre=nombre, series=series, dia=dia, nota=nota)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/eliminar/<int:id>')
def eliminar(id):
    ejercicio = Ejercicio.query.get(id)
    db.session.delete(ejercicio)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/resetear')
def resetear():
    ejercicios = Ejercicio.query.all()
    for e in ejercicios:
        e.completado = False
    db.session.commit()
    return redirect(url_for('admin'))

# Servir React
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)