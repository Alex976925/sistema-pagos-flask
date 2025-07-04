# redir.py
from flask import Flask, redirect

app = Flask(__name__)

@app.route('/')
def redirigir():
    try:
        with open("url_actual.txt", "r") as f:
            url = f.read().strip()
        return redirect(url, code=302)
    except FileNotFoundError:
        return "⛔ Aún no hay URL generada por cloudflared", 503

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)
