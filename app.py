from flask import Flask, render_template,request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import stripe

app = Flask(__name__)
app.secret_key = 'supersecret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Stripe keys
STRIPE_SECRET_KEY = 'sk_test_TU_CLAVE_PRIVADA'
STRIPE_PUBLIC_KEY = 'pk_test_TU_CLAVE_PUBLICA'
stripe.api_key = STRIPE_SECRET_KEY
PAYPAL_CLIENT_ID = 'TU_CLIENT_ID'

# ─────── MODELOS ───────
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True)
    clave_hash = db.Column(db.String(200))

class Empleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    apellido = db.Column(db.String(50))
    numero = db.Column(db.String(20))
    correo = db.Column(db.String(100))
    direccion = db.Column(db.String(100))
    puesto = db.Column(db.String(50))
    sueldo = db.Column(db.Float)

class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    contacto = db.Column(db.String(100))

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    proveedor = db.Column(db.String(100))
    costo_paquete = db.Column(db.Float)
    piezas_diarias = db.Column(db.Integer)
    tiempo_venta_caja = db.Column(db.String(50))

class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)

# ─────── AUTENTICACIÓN ───────
def login_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorada

# ─────── CREAR DB + USUARIO ───────
if not os.path.exists('data.db'):
    with app.app_context():
        db.create_all()
        if not Usuario.query.filter_by(usuario='admin').first():
            admin = Usuario(usuario='admin', clave_hash=generate_password_hash('1234'))
            db.session.add(admin)
            db.session.commit()

# ─────── RUTAS ───────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        clave = request.form.get("clave")
        u = Usuario.query.filter_by(usuario=usuario).first()
        if u and check_password_hash(u.clave_hash, clave):
            session["user"] = usuario
            return redirect(url_for("index"))
        else:
            return render_template("login_error.html")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/empleados", methods=["GET", "POST"])
@login_requerido
def empleados():
    if request.method == "POST":
        e = Empleado(
            nombre=request.form.get("nombre"),
            apellido=request.form.get("apellido"),
            numero=request.form.get("numero"),
            correo=request.form.get("correo"),
            direccion=request.form.get("direccion"),
            puesto=request.form.get("puesto"),
            sueldo=float(request.form.get("sueldo", 0))
        )
        db.session.add(e)
        db.session.commit()
        return redirect(url_for("empleados"))
    empleados = Empleado.query.all()
    return render_template("empleados.html", empleados=empleados)

@app.route("/proveedores", methods=["GET", "POST"])
@login_requerido
def proveedores():
    if request.method == "POST":
        p = Proveedor(
            nombre=request.form.get("nombre"),
            contacto=request.form.get("contacto")
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("proveedores"))
    proveedores = Proveedor.query.all()
    return render_template("proveedores.html", proveedores=proveedores)

@app.route("/productos", methods=["GET", "POST"])
@login_requerido
def productos():
    if request.method == "POST":
        p = Producto(
            nombre=request.form.get("nombre"),
            proveedor=request.form.get("proveedor"),
            costo_paquete=float(request.form.get("costo_paquete", 0)),
            piezas_diarias=int(request.form.get("piezas_diarias", 0)),
            tiempo_venta_caja=request.form.get("tiempo_venta_caja")
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("productos"))
    productos = Producto.query.all()
    return render_template("productos.html", productos=productos)

@app.route("/pagos", methods=["GET", "POST"])
@login_requerido
def pagos():
    if request.method == "POST":
        p = Pago(
            concepto=request.form.get("concepto"),
            monto=float(request.form.get("monto", 0))
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("pagos"))
    pagos = Pago.query.all()
    return render_template("pagos.html", pagos=pagos, stripe_key=STRIPE_PUBLIC_KEY, paypal_id=PAYPAL_CLIENT_ID)

@app.route("/analisis")
@login_requerido
def analisis():
    productos = Producto.query.all()
    return render_template("analisis.html", productos=productos)

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        clave = request.form.get("clave")
        if Usuario.query.filter_by(usuario=usuario).first():
            return "Ese usuario ya existe"
        nuevo = Usuario(usuario=usuario, clave_hash=generate_password_hash(clave))
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("registro.html")

# ─────── Stripe Checkout ───────
@app.route("/pagar_stripe", methods=["POST"])
@login_requerido
def pagar_stripe():
    data = request.get_json()
    monto = int(float(data.get("monto", 0)) * 100)
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                'price_data': {
                    'currency': 'mxn',
                    'product_data': {'name': 'Pago en sistema'},
                    'unit_amount': monto,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('pagos', _external=True),
            cancel_url=url_for('pagos', _external=True),
        )
        return jsonify({'url': session.url})
    except Exception as e:
        return jsonify({'error': str(e)})

# ─────── Ejecutar ───────
if __name__ == "__main__":
    app.run(debug=True)
