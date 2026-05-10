import os
from datetime import date, timedelta
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
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'None'

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
    dias_plan = db.relationship('DiaPlan', backref='usuario', lazy=True)
    nutricion = db.relationship('Nutricion', backref='usuario', lazy=True)
    suplementos = db.relationship('Suplemento', backref='usuario', lazy=True)

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    series = db.Column(db.String(50), nullable=False)
    completado = db.Column(db.Boolean, default=False)
    dia = db.Column(db.String(50), nullable=False, default='Lunes')
    nota = db.Column(db.String(200), nullable=True)
    reseteado_semana = db.Column(db.Date, nullable=True)
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

class RegistroSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ejercicio_id = db.Column(db.Integer, db.ForeignKey('ejercicio.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    peso = db.Column(db.Float, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    rpe = db.Column(db.Float, nullable=True)
    fecha = db.Column(db.Date, nullable=False)
    numero_set = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "ejercicio_id": self.ejercicio_id,
            "peso": self.peso,
            "reps": self.reps,
            "rpe": self.rpe,
            "fecha": self.fecha.isoformat(),
            "numero_set": self.numero_set,
        }

class DiaPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dia = db.Column(db.String(50), nullable=False)
    enfoque = db.Column(db.String(100), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "dia": self.dia,
            "enfoque": self.enfoque,
        }

class Nutricion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    subtitulo = db.Column(db.String(100), nullable=True)
    contenido = db.Column(db.Text, nullable=True)
    valor = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    orden = db.Column(db.Integer, default=0)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "subtitulo": self.subtitulo or "",
            "contenido": self.contenido.split("|") if self.contenido else [],
            "valor": self.valor or "",
            "color": self.color or "#2EC4B6",
            "orden": self.orden,
        }

class Suplemento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dosis = db.Column(db.String(100), nullable=False)
    prioridad = db.Column(db.String(20), nullable=False, default='Media')
    color = db.Column(db.String(20), nullable=False, default='#2EC4B6')
    razon = db.Column(db.Text, nullable=False)
    orden = db.Column(db.Integer, default=0)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "dosis": self.dosis,
            "prioridad": self.prioridad,
            "color": self.color,
            "razon": self.razon,
            "orden": self.orden,
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

    ambar = Usuario.query.filter_by(es_admin=False).first()
    if ambar and DiaPlan.query.filter_by(usuario_id=ambar.id).count() == 0:
        dias_plan = [
            DiaPlan(dia="Viernes", enfoque="Espalda · Bíceps", usuario_id=ambar.id),
            DiaPlan(dia="Sábado", enfoque="Piernas · Glúteo", usuario_id=ambar.id),
            DiaPlan(dia="Domingo", enfoque="Pecho · Hombros · Tríceps", usuario_id=ambar.id),
        ]
        db.session.add_all(dias_plan)
        db.session.commit()

    if ambar and Nutricion.query.filter_by(usuario_id=ambar.id).count() == 0:
        nutricion = [
            Nutricion(tipo="objetivo", titulo="Calorías", valor="Déficit moderado", subtitulo="~300 kcal menos", color="#FF6B35", orden=0, usuario_id=ambar.id),
            Nutricion(tipo="objetivo", titulo="Proteína", valor="120–140", subtitulo="g/día", color="#2EC4B6", orden=1, usuario_id=ambar.id),
            Nutricion(tipo="objetivo", titulo="Carbos", valor="Moderados", subtitulo="prioriza fibra", color="#5C6BC0", orden=2, usuario_id=ambar.id),
            Nutricion(tipo="objetivo", titulo="Grasas", valor="Saludables", subtitulo="aguacate, nueces", color="#E91E8C", orden=3, usuario_id=ambar.id),
            Nutricion(tipo="comida", titulo="Proteína primero", subtitulo="En cada comida", contenido="Empieza siempre por carne, huevo o frijoles|Satura antes y reduce calorías sin contar nada|Aplica en comedor del trabajo también", valor="↑ saciedad", orden=0, usuario_id=ambar.id),
            Nutricion(tipo="comida", titulo="Reducir calorías invisibles", subtitulo="Durante el día", contenido="Bebidas azucaradas → agua o agua mineral|Snacks entre comidas → fruta o nada|Pan extra → saltar o reducir", valor="fácil déficit", orden=1, usuario_id=ambar.id),
            Nutricion(tipo="comida", titulo="Agregar volumen sin calorías", subtitulo="Antes o durante comidas", contenido="Pepino, jícama, lechuga — llenan sin engordar|Agua antes de comer|Verduras extra si puedes pedir", valor="sin costo", orden=2, usuario_id=ambar.id),
            Nutricion(tipo="comida", titulo="No saltarse comidas", subtitulo="Regla general", contenido="Saltarse comidas lleva a comer de más después|Mejor comer poco que no comer|Snack ligero > hambre acumulada", valor="⚠️ importante", orden=3, usuario_id=ambar.id),
            Nutricion(tipo="regla", titulo="Proteína primero en cada comida — sin excepción", orden=0, usuario_id=ambar.id),
            Nutricion(tipo="regla", titulo="No contar calorías si no controlas lo que te sirven", orden=1, usuario_id=ambar.id),
            Nutricion(tipo="regla", titulo="Cortar bebidas azucaradas es el cambio más fácil y efectivo", orden=2, usuario_id=ambar.id),
            Nutricion(tipo="regla", titulo="Llevar tupperware cuando puedas — pollo + arroz + verdura", orden=3, usuario_id=ambar.id),
            Nutricion(tipo="regla", titulo="Hidratarse bien — el hambre falsa a veces es sed", orden=4, usuario_id=ambar.id),
        ]
        db.session.add_all(nutricion)
        db.session.commit()

    if ambar and Suplemento.query.filter_by(usuario_id=ambar.id).count() == 0:
        suplementos = [
            Suplemento(nombre="Proteína Whey", dosis="1 scoop post-entrenamiento", prioridad="Alta", color="#FF6B35", razon="Cubre el pico de síntesis proteica post-entreno cuando no puedes comer de inmediato.", orden=0, usuario_id=ambar.id),
            Suplemento(nombre="Creatina Monohidrato", dosis="5g diarios — cualquier momento", prioridad="Alta", color="#2EC4B6", razon="El suplemento más estudiado. Fuerza, volumen muscular y recuperación.", orden=1, usuario_id=ambar.id),
            Suplemento(nombre="Vitamina D3", dosis="2,000 UI con comida", prioridad="Media", color="#5C6BC0", razon="Inmunidad, estado de ánimo y metabolismo general.", orden=2, usuario_id=ambar.id),
            Suplemento(nombre="Magnesio Glicinato", dosis="300mg antes de dormir", prioridad="Media", color="#E91E8C", razon="Mejora calidad del sueño y recuperación muscular.", orden=3, usuario_id=ambar.id),
        ]
        db.session.add_all(suplementos)
        db.session.commit()

# ─── Reseteo semanal ───────────────────────────────────────
def verificar_reseteo_semanal(usuario_id):
    hoy = date.today()
    ultimo_lunes = hoy - timedelta(days=hoy.weekday())
    ejercicios = Ejercicio.query.filter_by(usuario_id=usuario_id).all()
    necesita_reset = any(
        e.reseteado_semana is None or e.reseteado_semana < ultimo_lunes
        for e in ejercicios
    )
    if necesita_reset:
        for e in ejercicios:
            e.completado = False
            e.reseteado_semana = hoy
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
    login_user(usuario, remember=True)
    return jsonify({"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email, "es_admin": usuario.es_admin})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = Usuario.query.filter_by(email=data['email']).first()
    if not usuario or not check_password_hash(usuario.password, data['password']):
        return jsonify({"error": "Credenciales incorrectas"}), 401
    login_user(usuario, remember=True)
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
    verificar_reseteo_semanal(current_user.id)
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

# ─── API dias plan ─────────────────────────────────────────
@app.route('/api/dias-plan')
@login_required
def get_dias_plan():
    dias = DiaPlan.query.filter_by(usuario_id=current_user.id).all()
    return jsonify([d.to_dict() for d in dias])

# ─── API nutricion ─────────────────────────────────────────
@app.route('/api/nutricion')
@login_required
def get_nutricion():
    items = Nutricion.query.filter_by(usuario_id=current_user.id).order_by(Nutricion.orden).all()
    return jsonify([n.to_dict() for n in items])

# ─── API suplementos ───────────────────────────────────────
@app.route('/api/suplementos')
@login_required
def get_suplementos():
    items = Suplemento.query.filter_by(usuario_id=current_user.id).order_by(Suplemento.orden).all()
    return jsonify([s.to_dict() for s in items])

# ─── Panel admin ───────────────────────────────────────────
@app.route('/admin')
def admin():
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    usuarios = Usuario.query.filter_by(es_admin=False).all()
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
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

@app.route('/admin-logout')
def admin_logout():
    logout_user()
    return redirect('/admin-login')

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

@app.route('/agregar-suplemento', methods=['POST'])
def agregar_suplemento():
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    usuario_id = int(request.form['usuario_id'])
    nuevo = Suplemento(
        nombre=request.form['nombre'],
        dosis=request.form['dosis'],
        prioridad=request.form['prioridad'],
        color=request.form['color'],
        razon=request.form['razon'],
        usuario_id=usuario_id
    )
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/eliminar-suplemento/<int:id>')
def eliminar_suplemento(id):
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    s = Suplemento.query.get(id)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/agregar-nutricion', methods=['POST'])
def agregar_nutricion():
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    usuario_id = int(request.form['usuario_id'])
    nuevo = Nutricion(
        tipo=request.form['tipo'],
        titulo=request.form['titulo'],
        subtitulo=request.form.get('subtitulo', ''),
        contenido=request.form.get('contenido', ''),
        valor=request.form.get('valor', ''),
        color=request.form.get('color', '#2EC4B6'),
        usuario_id=usuario_id
    )
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/eliminar-nutricion/<int:id>')
def eliminar_nutricion(id):
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    n = Nutricion.query.get(id)
    db.session.delete(n)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/agregar-dia-plan', methods=['POST'])
def agregar_dia_plan():
    if not current_user.is_authenticated or not current_user.es_admin:
        return redirect('/admin-login')
    usuario_id = int(request.form['usuario_id'])
    dia = request.form['dia']
    enfoque = request.form['enfoque']
    existente = DiaPlan.query.filter_by(usuario_id=usuario_id, dia=dia).first()
    if existente:
        existente.enfoque = enfoque
    else:
        nuevo = DiaPlan(dia=dia, enfoque=enfoque, usuario_id=usuario_id)
        db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('admin'))

# ─── API registro de sets ──────────────────────────────────
@app.route('/api/sets/<int:ejercicio_id>', methods=['GET'])
@login_required
def get_sets(ejercicio_id):
    hoy = date.today()
    sets = RegistroSet.query.filter_by(
        ejercicio_id=ejercicio_id,
        usuario_id=current_user.id,
        fecha=hoy
    ).order_by(RegistroSet.numero_set).all()
    return jsonify([s.to_dict() for s in sets])

@app.route('/api/sets/<int:ejercicio_id>', methods=['POST'])
@login_required
def agregar_set(ejercicio_id):
    data = request.get_json()
    hoy = date.today()
    numero = RegistroSet.query.filter_by(
        ejercicio_id=ejercicio_id,
        usuario_id=current_user.id,
        fecha=hoy
    ).count() + 1
    nuevo = RegistroSet(
        ejercicio_id=ejercicio_id,
        usuario_id=current_user.id,
        peso=data.get('peso'),
        reps=data.get('reps'),
        rpe=data.get('rpe'),
        fecha=hoy,
        numero_set=numero
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify(nuevo.to_dict())

@app.route('/api/sets/<int:set_id>/eliminar', methods=['DELETE'])
@login_required
def eliminar_set(set_id):
    s = RegistroSet.query.get(set_id)
    if s.usuario_id != current_user.id:
        return jsonify({"error": "No autorizado"}), 403
    db.session.delete(s)
    db.session.commit()
    return jsonify({"ok": True})

@app.route('/api/historial/<int:ejercicio_id>', methods=['GET'])
@login_required
def get_historial(ejercicio_id):
    sets = RegistroSet.query.filter_by(
        ejercicio_id=ejercicio_id,
        usuario_id=current_user.id,
    ).order_by(RegistroSet.fecha.desc(), RegistroSet.numero_set).limit(30).all()
    return jsonify([s.to_dict() for s in sets])

# ─── Servir React ──────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)