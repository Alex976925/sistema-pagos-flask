# 💸 Sistema de Pagos con Flask

Este proyecto es una plataforma web construida con Python y Flask que permite realizar pagos locales e internacionales mediante *Stripe* (tarjetas y Google Pay) y *PayPal REST API real*. Pensado para empresas en Latinoamérica que necesitan conversión de moneda, historial de pagos, y una interfaz sencilla.

---

## 📸 Captura de pantalla

![Demo del sistema de pagos](static/demo.png)

⚠️ Para mostrar esta imagen, guarda una captura de pantalla de tu sistema como `demo.png` dentro de tu carpeta `static/`. Luego sube ese archivo y haz commit.


---

## 🚀 ¿Cómo usarlo?

1. Regístrate como empresa desde la web.
2. Inicia sesión.
3. Ingresa un monto y selecciona moneda.
4. El sistema convierte automáticamente el valor.
5. Realiza el pago con:
   - 🟦 Stripe (tarjetas / Google Pay)
   - 🟨 PayPal (API REST real, no sandbox)
6. Consulta el historial de tus transacciones en la misma página.

---

## ⚙️ Instalación

```bash
git clone https://github.com/Alex976925/sistema-pagos-flask.git
cd sistema-pagos-flask
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python app.py
