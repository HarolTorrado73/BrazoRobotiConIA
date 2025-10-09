#!/bin/bash

# Script de instalación para Brazo Robótico en Raspberry Pi 5
# Configura entorno virtual y dependencias

echo "🚀 INSTALACIÓN DEL BRAZO ROBÓTICO - RASPBERRY PI 5"
echo "================================================="

# Verificar que estamos en Raspberry Pi
if ! grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Advertencia: No se detectó Raspberry Pi 5. Continuando de todos modos..."
fi

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
echo "🔧 Instalando dependencias del sistema..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libatlas-base-dev \
    libjpeg-dev \
    libtiff-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libcanberra-gtk3-module \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-good1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    i2c-tools \
    libi2c-dev \
    python3-smbus \
    python3-rpi.gpio

# Habilitar interfaces
echo "🔌 Configurando interfaces..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_ssh 0

# Reiniciar servicios
sudo systemctl restart i2c
sudo systemctl restart camera

# Crear directorio del proyecto
PROJECT_DIR="$HOME/BrazoRobotico"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 Creando directorio del proyecto..."
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Configurar entorno virtual
echo "🐍 Configurando entorno virtual..."
python3 -m venv robot_env
source robot_env/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependencias Python
echo "📚 Instalando dependencias Python..."
pip install -r requirements.txt

# Configurar permisos GPIO
echo "🔐 Configurando permisos GPIO..."
sudo usermod -a -G gpio,i2c,video $USER

# Configurar UART para TMC2208
echo "⚙️  Configurando UART para TMC2208..."
sudo raspi-config nonint do_serial 1
sudo raspi-config nonint do_serial_cons 0

# Crear archivo de configuración inicial
echo "📝 Creando configuración inicial..."
cat > calibration_data.json << EOF
{
    "servo_offsets": {"base": 0, "shoulder": 0, "elbow": 0, "gripper": 0},
    "stepper_steps_per_mm": 100,
    "vision_calibration": {
        "focal_length": 1000,
        "image_center": [1296, 972],
        "scale_factor": 0.5
    },
    "arm_dimensions": {
        "base_height": 50,
        "upper_arm": 200,
        "forearm": 150,
        "gripper_offset": 50
    },
    "position_corrections": {}
}
EOF

# Probar instalación
echo "🧪 Probando instalación..."
python3 -c "
import sys
print('Python version:', sys.version)
try:
    import RPi.GPIO as GPIO
    print('✅ RPi.GPIO OK')
except ImportError as e:
    print('❌ RPi.GPIO Error:', e)

try:
    from adafruit_servokit import ServoKit
    print('✅ Adafruit ServoKit OK')
except ImportError as e:
    print('❌ Adafruit ServoKit Error:', e)

try:
    from picamera2 import Picamera2
    print('✅ Picamera2 OK')
except ImportError as e:
    print('❌ Picamera2 Error:', e)

try:
    import cv2
    print('✅ OpenCV OK')
except ImportError as e:
    print('❌ OpenCV Error:', e)

try:
    from tmc2209 import TMC2209
    print('✅ TMC2209 OK')
except ImportError as e:
    print('❌ TMC2209 Error:', e)
"

echo ""
echo "🎉 INSTALACIÓN COMPLETADA!"
echo "=========================="
echo ""
echo "Para activar el entorno virtual:"
echo "  source ~/BrazoRobotico/robot_env/bin/activate"
echo ""
echo "Para ejecutar el brazo robótico:"
echo "  cd ~/BrazoRobotico/hecho"
echo "  python3 main.py"
echo ""
echo "Para calibración:"
echo "  python3 calibration_system.py"
echo ""
echo "⚠️  IMPORTANTE: Reinicia la Raspberry Pi para aplicar todos los cambios:"
echo "  sudo reboot"
echo ""
echo "📖 Lee el README.md para más información"