#!/usr/bin/env python3
"""
Script de diagnóstico del sistema brazo robótico
"""

import sys
import subprocess

def verificar_modulo(modulo):
    try:
        __import__(modulo)
        return True, f"✅ {modulo}"
    except ImportError as e:
        return False, f"❌ {modulo}: {e}"

def ejecutar_comando(comando):
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        return resultado.returncode == 0, resultado.stdout.strip()
    except Exception as e:
        return False, str(e)

print("🔍 DIAGNÓSTICO DEL SISTEMA BRAZO ROBÓTICO")
print("=" * 50)

# Verificar módulos Python
modulos = ['adafruit_servokit', 'picamera2', 'cv2', 'RPi.GPIO', 'tmc2209']
print("\n1. VERIFICACIÓN DE MÓDULOS PYTHON:")
for modulo in modulos:
    estado, mensaje = verificar_modulo(modulo)
    print(f"   {mensaje}")

# Verificar interfaces hardware
print("\n2. VERIFICACIÓN DE INTERFACES HARDWARE:")
interfaces = [
    ("I2C", "sudo i2cdetect -y 1 | grep -q '40' && echo 'OK' || echo 'FALLO'"),
    ("Cámara", "vcgencmd get_camera"),
    ("GPIO", "python3 -c 'import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print(\"OK\")'")
]

for nombre, comando in interfaces:
    estado, resultado = ejecutar_comando(comando)
    print(f"   {nombre}: {'✅' if estado else '❌'} {resultado}")

print("\n3. RESUMEN:")
print("   Si todos los módulos muestran ✅, el sistema está listo.")
print("   Si hay ❌, revisa la instalación de dependencias.")