#!/usr/bin/env python3
"""
Servidor de control remoto para brazo robótico
Utiliza Flask-SocketIO para comunicación en tiempo real
"""

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import json
import logging
import threading
import time
from hecho.servo_controller import ServoController
from stepper_motor import StepperMotor
from vision_system import VisionSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobotServer:
    def __init__(self, host='0.0.0.0', port=5000):
        """
        Inicializa el servidor del robot
        """
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.host = host
        self.port = port

        # Componentes del robot
        self.servo_controller = None
        self.stepper_motor = None
        self.vision_system = None

        # Estado del robot
        self.status = {
            'connected': False,
            'servos': {},
            'motor_position': 0,
            'vision_active': False,
            'detected_objects': []
        }

        self.setup_routes()
        self.setup_socket_events()

        logger.info("RobotServer inicializado")

    def setup_routes(self):
        """
        Configura las rutas HTTP
        """
        @self.app.route('/')
        def index():
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Control de Brazo Robótico</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .control-panel { display: flex; flex-wrap: wrap; gap: 20px; }
                    .servo-control { border: 1px solid #ccc; padding: 10px; border-radius: 5px; }
                    .motor-control { border: 1px solid #ccc; padding: 10px; border-radius: 5px; }
                    .vision-panel { border: 1px solid #ccc; padding: 10px; border-radius: 5px; }
                    button { margin: 5px; padding: 8px 16px; }
                    input[type="range"] { width: 100%; }
                    #video { border: 1px solid #ccc; }
                </style>
            </head>
            <body>
                <h1>Control de Brazo Robótico con IA</h1>
                <div id="status">Estado: Desconectado</div>

                <div class="control-panel">
                    <div class="servo-control">
                        <h3>Servos</h3>
                        <div id="servo-sliders"></div>
                        <button onclick="homeServos()">Posición Inicial</button>
                        <button onclick="openGripper()">Abrir Pinza</button>
                        <button onclick="closeGripper()">Cerrar Pinza</button>
                    </div>

                    <div class="motor-control">
                        <h3>Motor Lineal</h3>
                        <button onclick="motorLeft()">◀ Izquierda</button>
                        <button onclick="motorRight()">Derecha ▶</button>
                        <button onclick="motorHome()">Inicio</button>
                        <br>
                        <input type="range" id="motor-speed" min="100" max="2000" value="1000">
                        <label for="motor-speed">Velocidad</label>
                    </div>

                    <div class="vision-panel">
                        <h3>Visión Artificial</h3>
                        <button onclick="startVision()">Iniciar Visión</button>
                        <button onclick="stopVision()">Detener Visión</button>
                        <br>
                        <video id="video" width="320" height="240" autoplay></video>
                        <br>
                        <div id="objects-list"></div>
                    </div>
                </div>

                <script>
                    const socket = io();

                    socket.on('connect', function() {
                        document.getElementById('status').textContent = 'Estado: Conectado';
                    });

                    socket.on('disconnect', function() {
                        document.getElementById('status').textContent = 'Estado: Desconectado';
                    });

                    socket.on('status_update', function(data) {
                        updateStatus(data);
                    });

                    socket.on('vision_frame', function(data) {
                        const video = document.getElementById('video');
                        video.src = 'data:image/jpeg;base64,' + data.frame;
                    });

                    function updateStatus(data) {
                        // Actualizar sliders de servos
                        const servoSliders = document.getElementById('servo-sliders');
                        servoSliders.innerHTML = '';
                        for (const [servo, angle] of Object.entries(data.servos)) {
                            servoSliders.innerHTML += `
                                <label>${servo}: ${angle}°</label>
                                <input type="range" id="${servo}-slider" min="0" max="180" value="${angle}"
                                       onchange="setServo('${servo}', this.value)">
                            `;
                        }

                        // Actualizar lista de objetos
                        const objectsList = document.getElementById('objects-list');
                        objectsList.innerHTML = '<h4>Objetos Detectados:</h4>';
                        data.detected_objects.forEach(obj => {
                            objectsList.innerHTML += `<div>${obj[5]}: ${obj[4].toFixed(2)}</div>`;
                        });
                    }

                    function setServo(servo, angle) {
                        socket.emit('set_servo', {servo: servo, angle: parseInt(angle)});
                    }

                    function homeServos() {
                        socket.emit('home_servos');
                    }

                    function openGripper() {
                        socket.emit('open_gripper');
                    }

                    function closeGripper() {
                        socket.emit('close_gripper');
                    }

                    function motorLeft() {
                        const speed = document.getElementById('motor-speed').value;
                        socket.emit('motor_move', {direction: -1, steps: 100, speed: parseInt(speed)});
                    }

                    function motorRight() {
                        const speed = document.getElementById('motor-speed').value;
                        socket.emit('motor_move', {direction: 1, steps: 100, speed: parseInt(speed)});
                    }

                    function motorHome() {
                        socket.emit('motor_home');
                    }

                    function startVision() {
                        socket.emit('start_vision');
                    }

                    function stopVision() {
                        socket.emit('stop_vision');
                    }
                </script>
            </body>
            </html>
            """)

    def setup_socket_events(self):
        """
        Configura los eventos de SocketIO
        """
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Cliente conectado")
            self.status['connected'] = True
            emit('status_update', self.status)

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info("Cliente desconectado")
            self.status['connected'] = False

        @self.socketio.on('initialize_robot')
        def handle_initialize():
            """Inicializa los componentes del robot"""
            try:
                self.servo_controller = ServoController()
                self.stepper_motor = StepperMotor()
                self.vision_system = VisionSystem()
                self.status['connected'] = True
                emit('status_update', self.status)
                logger.info("Robot inicializado")
            except Exception as e:
                logger.error(f"Error inicializando robot: {e}")
                emit('error', {'message': str(e)})

        @self.socketio.on('set_servo')
        def handle_set_servo(data):
            if self.servo_controller:
                try:
                    self.servo_controller.set_angle(data['servo'], data['angle'])
                    self.status['servos'] = self.servo_controller.angles
                    emit('status_update', self.status)
                except Exception as e:
                    emit('error', {'message': str(e)})

        @self.socketio.on('home_servos')
        def handle_home_servos():
            if self.servo_controller:
                self.servo_controller.home_position()
                self.status['servos'] = self.servo_controller.angles
                emit('status_update', self.status)

        @self.socketio.on('open_gripper')
        def handle_open_gripper():
            if self.servo_controller:
                self.servo_controller.open_gripper()
                self.status['servos'] = self.servo_controller.angles
                emit('status_update', self.status)

        @self.socketio.on('close_gripper')
        def handle_close_gripper():
            if self.servo_controller:
                self.servo_controller.close_gripper()
                self.status['servos'] = self.servo_controller.angles
                emit('status_update', self.status)

        @self.socketio.on('motor_move')
        def handle_motor_move(data):
            if self.stepper_motor:
                try:
                    steps = data['direction'] * data['steps']
                    self.stepper_motor.move_steps(steps, data.get('speed', 1000))
                    self.status['motor_position'] = self.stepper_motor.get_position()
                    emit('status_update', self.status)
                except Exception as e:
                    emit('error', {'message': str(e)})

        @self.socketio.on('motor_home')
        def handle_motor_home():
            if self.stepper_motor:
                self.stepper_motor.home()
                self.status['motor_position'] = self.stepper_motor.get_position()
                emit('status_update', self.status)

        @self.socketio.on('start_vision')
        def handle_start_vision():
            if self.vision_system:
                try:
                    self.vision_system.start_camera()
                    self.status['vision_active'] = True
                    # Iniciar hilo para enviar frames
                    threading.Thread(target=self._vision_stream).start()
                    emit('status_update', self.status)
                except Exception as e:
                    emit('error', {'message': str(e)})

        @self.socketio.on('stop_vision')
        def handle_stop_vision():
            if self.vision_system:
                self.vision_system.stop_camera()
                self.status['vision_active'] = False
                emit('status_update', self.status)

    def _vision_stream(self):
        """
        Envía frames de visión en tiempo real
        """
        import base64
        while self.vision_system and self.vision_system.running:
            frame = self.vision_system.get_frame()
            if frame is not None:
                # Codificar frame como JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                _, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                img_base64 = base64.b64encode(encoded_img.tobytes()).decode('utf-8')

                self.status['detected_objects'] = self.vision_system.detected_objects
                self.socketio.emit('vision_frame', {'frame': img_base64})
                self.socketio.emit('status_update', self.status)

            time.sleep(0.1)  # ~10 FPS

    def run(self):
        """
        Inicia el servidor
        """
        logger.info(f"Iniciando servidor en {self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port)

    def cleanup(self):
        """
        Limpia recursos
        """
        if self.vision_system:
            self.vision_system.cleanup()
        if self.stepper_motor:
            self.stepper_motor.cleanup()
        logger.info("RobotServer limpiado")

if __name__ == "__main__":
    server = RobotServer()
    try:
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        server.cleanup()