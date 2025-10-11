# Brazo Robótico Autónomo con Visión Artificial

Este repositorio guía en la construcción paso a paso de un brazo robótico autónomo con visión artificial, desde el nivel principiante. Incluye control de servomotores y motor paso a paso, detección de objetos con YOLO, y operación autónoma de pick & place.

## Componentes Hardware

- **Raspberry Pi 5** (2GB RAM) - Controlador principal
- **Servos MG996R** (4 unidades): base, hombro, codo, pinza
- **Motor NEMA 17** con reductor - Elevación del brazo
- **PCA9685** - Controlador I2C para servos (16 canales)
- **TMC2208** - Driver SilentStepStick para NEMA 17
- **Raspberry Pi Camera** - Visión artificial
- **Fuentes de alimentación**:
  - 5V/20A para servos
  - 12V/5A para NEMA 17 + TMC2208

## Instalación

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd BrazoRoboticoConIA
cd definitivo
```

### 2. Crear y activar entorno virtual
```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual
# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias del sistema
```bash
# En Ubuntu/Debian (necesario para la Raspberry Pi)
sudo apt update
sudo apt install -y \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-smbus \
    build-essential \
    git \
    i2c-tools \
    python3-rpi.gpio \
    python3-lgpio \     # Específico para Raspberry Pi 5
    python3-gpiozero \ # Para control GPIO de alto nivel
    libopencv-dev \
    python3-opencv \
    ffmpeg \
    libxml2-dev \
    libxslt1-dev \
    libdbus-1-dev \
    libglib2.0-dev \
    pkg-config \
    cmake \
    gcc \
    g++ \
    wget

# Para Raspberry Pi 5, necesitamos estos paquetes adicionales
sudo apt install -y \
    python3-lgpio \     # Nueva biblioteca GPIO para Pi 5
    python3-pigpio \    
    libpigpio1

# Configurar permisos y servicios para GPIO
sudo usermod -a -G gpio $USER    # Agregar usuario al grupo gpio
sudo systemctl enable pigpiod    # Habilitar el servicio GPIO
sudo systemctl start pigpiod     # Iniciar el servicio GPIO

# Habilitar I2C y la cámara
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_camera 0

# Agregar usuario al grupo i2c y video
sudo usermod -a -G i2c,video $USER
```

### 4. Instalar dependencias de Python
```bash
# Asegúrate de que el entorno virtual está activado (verás (venv) al inicio del prompt)
pip install --upgrade pip setuptools wheel

# Instalar bibliotecas GPIO específicas para Raspberry Pi 5
pip install rpi-lgpio adafruit-blinka

# Instalar bibliotecas para el controlador PCA9685
pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit

# Instalar torch para ARM (específico para Raspberry Pi)
pip install --extra-index-url https://www.piwheels.org/simple torch torchvision

# Instalar el resto de dependencias
pip install -r requirements.txt

# Verificar la instalación de GPIO
python -c "import board; print('GPIO configurado correctamente')"
```

### 5. Configurar I2C y GPIO
Asegúrate de que I2C esté habilitado en Raspberry Pi:
```bash
sudo raspi-config
# Interfacing Options > I2C > Enable
```

Instalar bibliotecas necesarias:
```bash
sudo apt update
sudo apt install python3-smbus python3-dev
```

## Configuración Hardware

### Conexiones PCA9685 (Servos)
- VCC: 5V
- GND: GND
- SDA: Pin 3 (GPIO 2)
- SCL: Pin 5 (GPIO 3)
- Canales 0-3: Servos MG996R (base, hombro, codo, pinza)
- Señal de servos: VCC (5V), GND

### Conexiones TMC2208 (NEMA 17)
- VM: 12V
- GND: GND
- STEP: GPIO 17 (Pin 11)
- DIR: GPIO 18 (Pin 12)
- ENABLE: GPIO 19 (Pin 35) - Opcional
- Motor: Conectar bobinas del NEMA 17

### Cámara
- Conectar Raspberry Pi Camera al puerto CSI

## Ejecución

### Ejecutar el sistema principal
```bash
cd arm_system
python main.py
```

### Menú de comandos
- `c`: Verificar servicios
- `s`: Servicio de seguridad
- `n`: Escanear entorno (captura imagen y detecta objetos)
- `p`: Pick & place (seleccionar objeto detectado)
- `q`: Salir

## Uso

1. Ejecuta el sistema.
2. Selecciona 'n' para escanear: captura imagen, detecta objetos con YOLO.
3. Selecciona 'p' para pick & place: elige objeto, el brazo se mueve para tomarlo y colocarlo en zona designada.
4. El sistema maneja automáticamente el control de servos y motor paso a paso.

## Notas

- Asegúrate de calibrar los servos antes de usar.
- Las zonas de colocación están predefinidas por clase de objeto.
- El sistema incluye protocolos de seguridad en caso de fallos.

## Próximos pasos

Optimización y expansión en cursos futuros.
