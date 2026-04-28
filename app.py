from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'
db = SQLAlchemy(app)

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    series = db.Column(db.String(50), nullable=False)
    completado = db.Column(db.Boolean, default=False)

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

@app.route('/')
def home():
    rutina = Ejercicio.query.all()
    return render_template('index.html', rutina=rutina)

@app.route('/marcar/<int:id>')
def marcar(id):
    ejercicio = Ejercicio.query.get(id)
    ejercicio.completado = not ejercicio.completado
    db.session.commit()
    return redirect(url_for('home'))

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

if __name__ == '__main__':
    app.run(debug=True)