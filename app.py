import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
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

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "series": self.series,
            "completado": self.completado
        }

with app.app_context():
    db.create_all()
    if Ejercicio.query.count() == 0:
        ejercicios = [
            Ejercicio(nombre="Peso muerto", series="3 x 5"),
            Ejercicio(nombre="Sentadilla frontal", series="4 x 10-12"),
            Ejercicio(nombre="Zancadas", series="3 x 12"),
            Ejercicio(nombre="Curl femoral", series="4 x 12"),
            Ejercicio(nombre="Pantorrillas", series="4 x 15"),
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
    rutina = Ejercicio.query.all()
    return render_template('admin.html', rutina=rutina)

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form['nombre']
    series = request.form['series']
    nuevo = Ejercicio(nombre=nombre, series=series)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/eliminar/<int:id>')
def eliminar(id):
    ejercicio =