# Brazo Robótico con Visión Artificial
## Raspberry Pi 5 + SHCHV 5MP Camera

Sistema completo de brazo robótico de 4 grados de libertad con capacidades de visión artificial, diseñado específicamente para Raspberry Pi 5.

## 🛠️ Componentes del Sistema

| Componente | Especificaciones | Estado |
|------------|------------------|--------|
| **Raspberry Pi 5** | 2GB RAM | ✅ Compatible |
| **Cámara SHCHV 5MP** | Sensor CSI, conexión flex | ✅ Integrada |
| **Servos MG996R** | 4 unidades (base, hombro, codo, pinza) | ✅ Controlados |
| **Motor NEMA 17** | Paso a paso con reductor | ✅ Controlado |
| **PCA9685** | Controlador I2C 16 canales | ✅ Implementado |
| **TMC2208** | Driver stepper SilentStepStick | ✅ Configurado |
| **Fuente 5V/20A** | Alimentación servos | ✅ Especificada |
| **Fuente 12V/5A** | Alimentación NEMA 17 + TMC2208 | ✅ Especificada |

## 🚀 Instalación Rápida

### 1. Clonar y configurar entorno
```bash
# Ejecutar script de instalación automática
./install.sh

# O instalar manualmente:
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
sudo apt upgrade
python3 -m venv robot_env
source robot_env/bin/activate
pip install adafruit-circuitpython-servokit==1.3.21
pip install RPi.GPIO==0.7.1
pip install git+https://github.com/chrisjbillington/TMC2209.git
pip install opencv-python==4.8.1.78
pip install picamera2==0.3.7
pip install numpy==1.24.3
pip install pillow==10.0.0
pip install flask==2.3.3
pip install python-socketio==5.8.0
pip install flask-socketio==5.3.6
pip install tensorflow==2.13.0
pip install pygame==2.5.0
pip install matplotlib==3.7.2
```

### 2. Configurar hardware
```bash
# Habilitar interfaces
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_serial 1

# Reiniciar
sudo reboot
```

### 3. Verificar instalación
```bash
source robot_env/bin/activate
cd hecho
python3 -c "from robot_arm import RobotArm; print('✅ Instalación exitosa')"
```

## 🎯 Uso del Sistema

### Modo Básico
```bash
# Activar entorno virtual
source ~/Documents/robot/robot_env/bin/activate
cd ~/Documents/robot/brazo/hecho

# Ejecutar brazo robótico
python3 main.py
```

### Calibración
```bash
# Sistema de calibración completo
python3 calibration_system.py

# Opciones:
# 1. Calibración completa automática
# 2. Pruebas diagnósticas
# 3. Medición de precisión
```

### Control Remoto
```bash
# Servidor web
python3 robot_server.py

# Cliente (desde otra máquina)
python3 robot_client.py
```

## 🔧 Configuración de Hardware

### Conexiones PCA9685 (Servos)
- **VCC**: 5V desde fuente de servos
- **GND**: GND común
- **SDA**: Pin 3 (GPIO 2) Raspberry Pi
- **SCL**: Pin 5 (GPIO 3) Raspberry Pi
- **Canales**:
  - Canal 0: Servo base
  - Canal 1: Servo hombro
  - Canal 2: Servo codo
  - Canal 3: Servo pinza

### Conexiones TMC2208 (Motor NEMA 17)
- **VM**: 12V desde fuente stepper
- **GND**: GND común
- **EN**: Pin 22 (GPIO 25) Raspberry Pi
- **DIR**: Pin 23 (GPIO 11) Raspberry Pi
- **STEP**: Pin 24 (GPIO 8) Raspberry Pi
- **UART TX/RX**: Conectados a UART del Pi

### Cámara SHCHV 5MP
- Conectar al puerto CSI de la Raspberry Pi 5
- Asegurar buena iluminación para visión artificial

## 📊 Características Técnicas

### Cinemática
- **Grados de libertad**: 4 (3 rotacionales + 1 prismatic)
- **Alcance**: ~35cm radial
- **Precisión**: ±1mm (con calibración)
- **Velocidad**: Ajustable 10-100% PWM

### Visión Artificial
- **Resolución**: 2592x1944 (5MP)
- **Frame rate**: 30 FPS
- **Procesamiento**: OpenCV + NumPy
- **Detección**: Color-based object tracking
- **Calibración**: Automática con marcadores

### Control
- **Protocolo**: I2C para servos, UART para stepper
- **Frecuencia PWM**: 50Hz (servos)
- **Microstepping**: 1/16 para NEMA 17
- **Interface**: WebSocket + REST API

## 🔍 Sistema de Calibración

### Calibración Automática
1. **Offsets de servos**: Ajuste automático basado en posiciones conocidas
2. **Corrección de posiciones**: Aprendizaje de errores sistemáticos
3. **Calibración visual**: Transformación imagen-mundo
4. **Verificación**: Tests de repetibilidad y precisión

### Medición de Precisión
```python
from calibration_system import CalibrationSystem
cal = CalibrationSystem()
results = cal.measure_position_accuracy()
print(f"Precisión promedio: {results}")
```

## 🐛 Solución de Problemas

### Error: "No se pudo abrir la cámara"
```bash
# Verificar configuración de cámara
vcgencmd get_camera
sudo raspi-config nonint do_camera 0
sudo reboot
```

### Error: "PCA9685 no encontrado"
```bash
# Verificar I2C
sudo i2cdetect -y 1
# Debe mostrar 40 en la dirección del PCA9685
```

### Error: "TMC2208 comunicación fallida"
```bash
# Verificar UART
ls /dev/serial*
# Configurar UART
sudo raspi-config nonint do_serial 1
sudo reboot
```

## 📈 Mejoras Recientes

### Versión 2.0 - Precisión Mejorada
- ✅ **Cinemática calibrada**: Offsets dinámicos desde JSON
- ✅ **Corrección de errores**: Aprendizaje de posiciones
- ✅ **Calibración automática**: Ajuste de offsets sin intervención
- ✅ **Visión integrada**: Picamera2 para Raspberry Pi 5
- ✅ **Control optimizado**: PCA9685 + TMC2208 nativos

## 🤝 Contribución

Para reportar bugs o sugerir mejoras:
1. Crear issue en el repositorio
2. Incluir logs de error
3. Especificar configuración de hardware

## 📄 Licencia

Este proyecto es open source bajo licencia MIT.

---

**Desarrollado para Raspberry Pi 5 con componentes estándar de robótica educativa.**