
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, abort
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Clave para firmar las sesiones.
# En producción, guardala en una variable de entorno.
app.secret_key = 'mi_clave_secreta_super_segura'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ==========================================
# Modelo de tarjetas
# ==========================================
class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)

    # Nullable permite conservar tarjetas antiguas sin propietario.
    user_email = db.Column(db.String(100), nullable=True)

    def __init__(self, title, subtitle, text, user_email):
        self.title = title
        self.subtitle = subtitle
        self.text = text
        self.user_email = user_email

    def __repr__(self):
        return f'<Card {self.id}>'


# ==========================================
# Modelo de usuarios
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def __repr__(self):
        return f'<User {self.email}>'


# ==========================================
# Crear tablas y migrar la columna faltante
# ==========================================
with app.app_context():
    db.create_all()

    inspector = inspect(db.engine)

    if 'card' in inspector.get_table_names():
        columnas = [
            columna['name']
            for columna in inspector.get_columns('card')
        ]

        if 'user_email' not in columnas:
            with db.engine.begin() as conn:
                conn.execute(
                    text(
                        'ALTER TABLE card '
                        'ADD COLUMN user_email VARCHAR(100)'
                    )
                )

            print('Columna user_email agregada correctamente.')


# ==========================================
# Protección de rutas
# ==========================================
@app.before_request
def guardia():
    # IMPORTANTE: permitir también las rutas POST.
    # Si login_post no es pública, nunca llega a validar
    # el correo y la contraseña del usuario.
    publicas = {
        'login',
        'login_post',
        'reg',
        'reg_post',
        'static'
    }

    # Algunas peticiones pueden no tener endpoint.
    if request.endpoint is None:
        return None

    if request.endpoint in publicas:
        return None

    # Todas las demás rutas requieren una sesión iniciada.
    if 'email' not in session:
        return redirect(url_for('login'))

    return None


# ==========================================
# Página principal
# ==========================================
@app.get('/')
def index():
    cards = (
        Card.query
        .filter_by(user_email=session['email'])
        .order_by(Card.id.desc())
        .all()
    )

    return render_template('index.html', cards=cards)


# ==========================================
# Ver tarjeta
# ==========================================
@app.get('/card/<int:id>')
def card(id):
    tarjeta = db.get_or_404(Card, id)

    # Cada usuario solamente puede ver sus propias tarjetas.
    if tarjeta.user_email != session['email']:
        abort(404)

    return render_template('card.html', card=tarjeta)


# ==========================================
# Crear tarjeta
# ==========================================
@app.get('/create')
def create():
    return render_template('create_card.html')


@app.post('/create')
def create_post():
    title = request.form.get('title', '').strip()
    subtitle = request.form.get('subtitle', '').strip()
    contenido = request.form.get('text', '').strip()

    if not title or not subtitle or not contenido:
        return render_template(
            'create_card.html',
            error='Completá todos los campos.'
        )

    nueva_tarjeta = Card(
        title=title,
        subtitle=subtitle,
        text=contenido,
        user_email=session['email']
    )

    db.session.add(nueva_tarjeta)
    db.session.commit()

    return redirect(url_for('index'))


# ==========================================
# Registro
# ==========================================
@app.get('/reg')
def reg():
    return render_template('registration.html')


@app.post('/reg')
def reg_post():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not email or not password:
        return render_template(
            'registration.html',
            error='Completá el correo y la contraseña.'
        )

    if User.query.filter_by(email=email).first():
        return render_template(
            'registration.html',
            error='Ese correo ya está registrado.'
        )

    usuario = User(
        email=email,
        password=generate_password_hash(password)
    )

    db.session.add(usuario)
    db.session.commit()

    return redirect(url_for('login', registered=1))


# ==========================================
# Inicio de sesión: formulario
# ==========================================
@app.get('/login')
def login():
    return render_template(
        'login.html',
        registered=request.args.get('registered')
    )


# ==========================================
# Inicio de sesión: validar credenciales
# ==========================================
@app.post('/login')
def login_post():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    usuario = User.query.filter_by(email=email).first()

    if usuario and check_password_hash(usuario.password, password):
        # Limpiar cualquier sesión anterior y crear la nueva.
        session.clear()
        session['email'] = usuario.email

        # Redirigir al diario con la sesión ya establecida.
        return redirect(url_for('index'))

    return render_template(
        'login.html',
        error='Correo o contraseña incorrectos.'
    ), 401


# ==========================================
# Cerrar sesión
# ==========================================
@app.get('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ==========================================
# Ejecutar aplicación
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)
