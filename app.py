import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-cambiar-en-produccion')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///fitness.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# ─── Modelos ───────────────────────────────────────────────
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    ejercicios = db.relationship('Ejercicio', backref='usuario', lazy=True)

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    series = db.Column(db.String(50), nullable=False)
    completado = db.Column(db.Boolean, default=False)
    dia = db.Column(db.String(50), nullable=False, default='Viernes')
    nota = db.Column(db.String(200), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "series": self.series,
            "completado": self.completado,
            "dia": self.dia,
            "nota": self.nota or "",
        }

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if Usuario.query.count() == 0:
        admin = Usuario(
            nombre="Edwin",
            email="edwincovarrubias20@gmail.com",
            password=generate_password_hash("admin123"),
            es_admin=True
        )
        db.session.add(admin)
        db.session.commit()

# ─── Auth endpoints ────────────────────────────────────────
@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.get_json()
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email ya registrado"}), 400
    usuario = Usuario(
        nombre=data['nombre'],
        email=data['email'],
        password=generate_password_hash(data['password'])
    )
    db.session.add(usuario)
    db.session.commit()
    login_user(usuario)
    return jsonify({"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email, "es_admin": usuario.es_admin})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = Usuario.query.filter_by(email=data['email']).first()
    if not usuario or not check_password_hash(usuario.password, data['password']):
        return jsonify({"error": "Credenciales incorrectas"}), 401
    login_user(usuario)
    return jsonify({"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email, "es_admin": usuario.es_admin})

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})

@app.route('/api/me')
def me():
    if current_user.is_authenticated:
        return jsonify({"id": current_user.id, "nombre": current_user.nombre, "email": current_user.email, "es_admin": current_user.es_admin})
    return jsonify({"error": "No autenticado"}), 401

# ─── API rutina ────────────────────────────────────────────
@app.route('/api/rutina')
@login_required
def get_rutina():
    rutina = Ejercicio.query.filter_by(usuario_id=current_user.id).all()
    return jsonify([e.to_dict() for e in rutina])

@app.route('/api/marcar/<int:id>', methods=['POST'])
@login_required
def marcar(id):
    ejercicio = Ejercicio.query.get(id)
    if ejercicio.usuario_id != current_user.id:
        return jsonify({"error": "No autorizado"}), 403
    ejercicio.completado = not ejercicio.completado
    db.session.commit()
    return jsonify(ejercicio.to_dict())

# ─── Panel admin ───────────────────────────────────────────
@app.route('/admin')
def admin():
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    usuarios = Usuario.query.filter_by(es_admin=False).all()
    dias = ["Viernes", "Sábado", "Domingo"]
    return render_template('admin.html', usuarios=usuarios, dias=dias)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.password, password) and usuario.es_admin:
            login_user(usuario)
            return redirect('/admin')
        return render_template('admin_login.html', error="Credenciales incorrectas")
    return render_template('admin_login.html')

@app.route('/agregar', methods=['POST'])
def agregar():
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    nombre = request.form['nombre']
    series = request.form['series']
    dia = request.form['dia']
    nota = request.form.get('nota', '')
    usuario_id = int(request.form['usuario_id'])
    nuevo = Ejercicio(nombre=nombre, series=series, dia=dia, nota=nota, usuario_id=usuario_id)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/eliminar/<int:id>')
def eliminar(id):
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    ejercicio = Ejercicio.query.get(id)
    db.session.delete(ejercicio)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/resetear/<int:usuario_id>')
def resetear(usuario_id):
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    ejercicios = Ejercicio.query.filter_by(usuario_id=usuario_id).all()
    for e in ejercicios:
        e.completado = False
    db.session.commit()
    return redirect(url_for('admin'))

# ─── Servir React ──────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)