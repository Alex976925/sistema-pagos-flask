import subprocess
import time
import re
import os

def iniciar_tunel():
    print("🚀 Iniciando Cloudflared...")
    proceso = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    url_publica = None
    while True:
        linea = proceso.stdout.readline()
        if "trycloudflare.com" in linea:
            match = re.search(r"(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)", linea)
            if match:
                url_publica = match.group(1)
                print(f"🌐 URL pública detectada: {url_publica}")
                with open("url_actual.txt", "w") as f:
                    f.write(url_publica)
                break
        if linea == '' and proceso.poll() is not None:
            print("❌ Cloudflared terminó inesperadamente")
            break
    return proceso

# Lanzar el túnel
while True:
    proceso = iniciar_tunel()
    # Espera y detecta si el túnel se cae
    while proceso.poll() is None:
        time.sleep(5)
    print("🔁 Reiniciando Cloudflared...")
    time.sleep(3)
