from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import stripe
import requests
from base64 import b64encode

app = Flask(__name__)
app.secret_key = 'supersecret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Stripe keys
STRIPE_SECRET_KEY = 'sk_test_TU_CLAVE_PRIVADA'
STRIPE_PUBLIC_KEY = 'pk_test_TU_CLAVE_PUBLICA'
stripe.api_key = STRIPE_SECRET_KEY

# PayPal keys
PAYPAL_CLIENT_ID = 'TU_CLIENT_ID'
PAYPAL_SECRET = 'TU_SECRET'

# Modelos
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

# Crear DB
if not os.path.exists('data.db'):
    with app.app_context():
        db.create_all()

# Rutas
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        clave = request.form["clave"]
        if usuario == "admin" and clave == "1234":
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
def empleados():
    if request.method == "POST":
        e = Empleado(
            nombre=request.form["nombre"],
            apellido=request.form["apellido"],
            numero=request.form["numero"],
            correo=request.form["correo"],
            direccion=request.form["direccion"],
            puesto=request.form["puesto"],
            sueldo=float(request.form["sueldo"])
        )
        db.session.add(e)
        db.session.commit()
        return redirect(url_for("empleados"))
    empleados = Empleado.query.all()
    return render_template("empleados.html", empleados=empleados)

@app.route("/proveedores", methods=["GET", "POST"])
def proveedores():
    if request.method == "POST":
        p = Proveedor(
            nombre=request.form["nombre"],
            contacto=request.form["contacto"]
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("proveedores"))
    proveedores = Proveedor.query.all()
    return render_template("proveedores.html", proveedores=proveedores)

@app.route("/productos", methods=["GET", "POST"])
def productos():
    if request.method == "POST":
        p = Producto(
            nombre=request.form["nombre"],
            proveedor=request.form["proveedor"],
            costo_paquete=float(request.form["costo_paquete"]),
            piezas_diarias=int(request.form["piezas_diarias"]),
            tiempo_venta_caja=request.form["tiempo_venta_caja"]
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("productos"))
    productos = Producto.query.all()
    return render_template("productos.html", productos=productos)

@app.route("/pagos", methods=["GET", "POST"])
def pagos():
    if request.method == "POST":
        p = Pago(
            concepto=request.form["concepto"],
            monto=float(request.form["monto"])
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("pagos"))
    pagos = Pago.query.all()
    return render_template("pagos.html", pagos=pagos, stripe_key=STRIPE_PUBLIC_KEY, paypal_id=PAYPAL_CLIENT_ID)

@app.route("/analisis")
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

# Stripe
@app.route("/pagar_stripe", methods=["POST"])
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

# PayPal
@app.route("/pagar_paypal", methods=["POST"])
def pagar_paypal():
    data = request.get_json()
    monto = data.get("monto", "0.00")

    auth = b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    res = requests.post("https://api-m.paypal.com/v1/oauth2/token", headers=headers, data={"grant_type": "client_credentials"})
    access_token = res.json().get("access_token")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "MXN",
                "value": monto
            }
        }],
        "application_context": {
            "return_url": url_for('pagos', _external=True),
            "cancel_url": url_for('pagos', _external=True)
        }
    }

    res = requests.post("https://api-m.paypal.com/v2/checkout/orders", headers=headers, json=body)
    data = res.json()
    url_aprobacion = next((link["href"] for link in data["links"] if link["rel"] == "approve"), None)
    return jsonify({"url": url_aprobacion})

if __name__ == "__main__":
    app.run(debug=True)
