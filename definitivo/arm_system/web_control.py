#!/usr/bin/env python3
"""
Web Interface for Robot Arm Control
Provides a web-based interface to control the robot arm with sliders and buttons
"""

from flask import Flask, render_template_string, request, jsonify
import time
import logging as log

try:
    from .control.robot_controller import ControladorRobotico
except ImportError:
    from control.robot_controller import ControladorRobotico

log.basicConfig(level=log.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

class ControladorWeb:
    """Controlador web para interfaz del brazo robótico"""

    def __init__(self):
        """Inicializar controlador web"""
        self.controlador_robot = ControladorRobotico()
        self.angulos_actuales = {
            'base': 180,
            'shoulder': 45,
            'elbow': 90,
            'gripper': 0
        }
        self.retardo_movimiento = 0.1  # Retardo entre movimientos
        self.velocidad = 2  # Velocidad más lenta para mejor precisión
        log.info("Controlador web inicializado")

    def movimiento_suave(self, articulación, ángulo_objetivo, pasos=10):
        """Movimiento suave interpolado"""
        try:
            ángulo_actual = self.angulos_actuales[articulación]
            tamaño_paso = (ángulo_objetivo - ángulo_actual) / pasos

            for paso in range(pasos):
                ángulo_intermedio = int(ángulo_actual + (tamaño_paso * (paso + 1)))

                if articulación == 'base':
                    self.controlador_robot.mover_base(ángulo_intermedio, velocidad=self.velocidad)
                elif articulación == 'shoulder':
                    self.controlador_robot.mover_hombro(ángulo_intermedio, velocidad=self.velocidad)
                elif articulación == 'elbow':
                    self.controlador_robot.mover_codo(ángulo_intermedio, velocidad=self.velocidad)
                elif articulación == 'gripper':
                    self.controlador_robot.mover_pinza(ángulo_intermedio, velocidad=self.velocidad)

                time.sleep(self.retardo_movimiento / pasos)

            self.angulos_actuales[articulación] = ángulo_objetivo
            return True, f"{articulación.title()} movido suavemente a {ángulo_objetivo}°"

        except Exception as e:
            return False, f"Error en movimiento suave {articulación}: {e}"

    def mover_articulación(self, articulación, ángulo):
        """Mover articulación específica con validación"""
        try:
            ángulo = int(ángulo)

            # Validar rangos para servos continuos
            límites_articulación = {
                'base': (0, 360),      # 180° = parar, <180° = giro horario, >180° = giro antihorario
                'shoulder': (0, 360),  # Control de velocidad
                'elbow': (0, 360),     # Control de velocidad
                'gripper': (0, 360)    # Control de velocidad
            }

            ángulo_min, ángulo_max = límites_articulación[articulación]
            if not (ángulo_min <= ángulo <= ángulo_max):
                return False, f"Ángulo de {articulación.title()} debe estar entre {ángulo_min}-{ángulo_max}°"

            # Usar movimiento suave para cambios grandes
            ángulo_actual = self.angulos_actuales[articulación]
            diferencia_ángulo = abs(ángulo - ángulo_actual)

            if diferencia_ángulo > 30:  # Movimiento grande, usar interpolación
                return self.movimiento_suave(articulación, ángulo, pasos=min(diferencia_ángulo // 5, 20))
            else:
                # Movimiento directo para cambios pequeños
                if articulación == 'base':
                    self.controlador_robot.mover_base(ángulo, velocidad=self.velocidad)
                elif articulación == 'shoulder':
                    self.controlador_robot.mover_hombro(ángulo, velocidad=self.velocidad)
                elif articulación == 'elbow':
                    self.controlador_robot.mover_codo(ángulo, velocidad=self.velocidad)
                elif articulación == 'gripper':
                    self.controlador_robot.mover_pinza(ángulo, velocidad=self.velocidad)

                time.sleep(self.retardo_movimiento)
                self.angulos_actuales[articulación] = ángulo
                return True, f"{articulación.title()} movido a {ángulo}°"

        except Exception as e:
            return False, f"Error moviendo {articulación}: {e}"

    def ir_a_home(self):
        """Mover a posición home suavemente"""
        try:
            posiciones_home = [
                ('base', 180),
                ('shoulder', 45),
                ('elbow', 90),
                ('gripper', 0)
            ]

            for articulación, ángulo in posiciones_home:
                éxito, mensaje = self.movimiento_suave(articulación, ángulo, pasos=15)
                if not éxito:
                    return False, mensaje
                time.sleep(0.3)

            self.angulos_actuales = {'base': 180, 'shoulder': 45, 'elbow': 90, 'gripper': 0}
            return True, "Movido suavemente a posición home"
        except Exception as e:
            return False, f"Error yendo a home: {e}"

    def secuencia_prueba(self):
        """Ejecutar secuencia de prueba suave"""
        try:
            posiciones_prueba = [
                ('base', 90),
                ('shoulder', 60),
                ('elbow', 120),
                ('gripper', 90),
                ('base', 270),
                ('shoulder', 30),
                ('elbow', 60),
                ('gripper', 45)
            ]

            for articulación, ángulo in posiciones_prueba:
                éxito, mensaje = self.movimiento_suave(articulación, ángulo, pasos=20)
                if not éxito:
                    return False, mensaje
                time.sleep(0.5)

            # Regresar a home
            self.ir_a_home()
            return True, "Secuencia de prueba suave completada"
        except Exception as e:
            return False, f"Prueba fallida: {e}"

# Instancia global del controlador
controlador = ControladorWeb()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control de Brazo Robótico</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .controls {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        .joint-control {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border: 2px solid #e9ecef;
        }
        .joint-control h3 {
            margin-top: 0;
            color: #495057;
            font-size: 1.4em;
            text-align: center;
        }
        .slider-container {
            margin: 20px 0;
        }
        .slider {
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: #ddd;
            outline: none;
            appearance: none;
        }
        .slider::-webkit-slider-thumb {
            appearance: none;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .slider::-moz-range-thumb {
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .angle-display {
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
            color: #495057;
            margin: 10px 0;
        }
        .buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-success {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
        }
        .btn-warning {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .btn-warning:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(240, 147, 251, 0.4);
        }
        .status {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
            border-left: 5px solid #28a745;
        }
        .status.error {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        .status.success {
            border-left-color: #28a745;
            background: #d4edda;
        }
        .current-angles {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        .angle-box {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .angle-box h4 {
            margin: 0 0 5px 0;
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        .angle-box .value {
            font-size: 1.5em;
            font-weight: bold;
            color: #495057;
        }
        @media (max-width: 768px) {
            .controls {
                grid-template-columns: 1fr;
            }
            .current-angles {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Control de Brazo Robótico</h1>
            <p>Interfaz web para control preciso de articulaciones</p>
        </div>

        <div class="controls">
            <!-- Base Control -->
            <div class="joint-control">
                <h3>🔄 Base (Velocidad)</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="360" value="180" class="slider" id="base-slider">
                </div>
                <div class="angle-display" id="base-angle">STOP</div>
                <div class="buttons">
                    <button class="btn btn-primary" onclick="setAngle('base', 90)">← Izq</button>
                    <button class="btn btn-primary" onclick="setAngle('base', 180)">STOP</button>
                    <button class="btn btn-primary" onclick="setAngle('base', 270)">Der →</button>
                </div>
            </div>

            <!-- Shoulder Control -->
            <div class="joint-control">
                <h3>💪 Hombro (Velocidad)</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="360" value="180" class="slider" id="shoulder-slider">
                </div>
                <div class="angle-display" id="shoulder-angle">STOP</div>
                <div class="buttons">
                    <button class="btn btn-primary" onclick="setAngle('shoulder', 90)">↑ Subir</button>
                    <button class="btn btn-primary" onclick="setAngle('shoulder', 180)">STOP</button>
                    <button class="btn btn-primary" onclick="setAngle('shoulder', 270)">↓ Bajar</button>
                </div>
            </div>

            <!-- Elbow Control -->
            <div class="joint-control">
                <h3>🦾 Codo (Velocidad)</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="360" value="180" class="slider" id="elbow-slider">
                </div>
                <div class="angle-display" id="elbow-angle">STOP</div>
                <div class="buttons">
                    <button class="btn btn-primary" onclick="setAngle('elbow', 90)">↑ Extender</button>
                    <button class="btn btn-primary" onclick="setAngle('elbow', 180)">STOP</button>
                    <button class="btn btn-primary" onclick="setAngle('elbow', 270)">↓ Contraer</button>
                </div>
            </div>

            <!-- Gripper Control -->
            <div class="joint-control">
                <h3>✋ Pinza (Velocidad)</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="360" value="180" class="slider" id="gripper-slider">
                </div>
                <div class="angle-display" id="gripper-angle">STOP</div>
                <div class="buttons">
                    <button class="btn btn-success" onclick="setAngle('gripper', 90)">Abrir</button>
                    <button class="btn btn-primary" onclick="setAngle('gripper', 180)">STOP</button>
                    <button class="btn btn-warning" onclick="setAngle('gripper', 270)">Cerrar</button>
                </div>
            </div>
        </div>

        <!-- Action Buttons -->
        <div style="padding: 30px; text-align: center;">
            <button class="btn btn-success" style="font-size: 1.2em; padding: 15px 30px; margin: 0 10px;" onclick="goHome()">
                🏠 Ir a Home
            </button>
            <button class="btn btn-warning" style="font-size: 1.2em; padding: 15px 30px; margin: 0 10px;" onclick="testSequence()">
                🧪 Probar Movimientos
            </button>
        </div>

        <!-- Configuración de Movimiento -->
        <div style="padding: 20px; background: #f8f9fa; margin: 20px; border-radius: 10px;">
            <h3 style="text-align: center; color: #495057;">⚙️ Configuración de Movimiento</h3>
            <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                <div>
                    <label style="display: block; margin-bottom: 5px;">Velocidad:</label>
                    <select id="speed-select" onchange="updateSpeed(this.value)">
                        <option value="1">Muy Lenta</option>
                        <option value="2" selected>Lenta</option>
                        <option value="3">Normal</option>
                        <option value="5">Rápida</option>
                    </select>
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px;">Suavizado:</label>
                    <select id="smooth-select" onchange="updateSmoothing(this.value)">
                        <option value="5">Mínimo</option>
                        <option value="10" selected>Normal</option>
                        <option value="20">Máximo</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="emergencyStop()">
                    🚫 Parada de Emergencia
                </button>
            </div>
        </div>

        <!-- Current Angles Display -->
        <div class="current-angles">
            <div class="angle-box">
                <h4>Base</h4>
                <div class="value" id="current-base">{{ angles.base }}°</div>
            </div>
            <div class="angle-box">
                <h4>Hombro</h4>
                <div class="value" id="current-shoulder">{{ angles.shoulder }}°</div>
            </div>
            <div class="angle-box">
                <h4>Codo</h4>
                <div class="value" id="current-elbow">{{ angles.elbow }}°</div>
            </div>
            <div class="angle-box">
                <h4>Pinza</h4>
                <div class="value" id="current-gripper">{{ angles.gripper }}°</div>
            </div>
        </div>

        <!-- Status Messages -->
        <div id="status" class="status" style="display: none;"></div>
    </div>

    <script>
        // Update angle displays in real-time for continuous servos
        function updateSpeedDisplay(sliderId, displayId) {
            const slider = document.getElementById(sliderId);
            const display = document.getElementById(displayId);

            slider.addEventListener('input', function() {
                const value = parseInt(this.value);
                if (value < 120) {
                    display.textContent = '← Rápido';
                } else if (value < 150) {
                    display.textContent = '← Medio';
                } else if (value < 210) {
                    display.textContent = 'STOP';
                } else if (value < 240) {
                    display.textContent = '→ Medio';
                } else {
                    display.textContent = '→ Rápido';
                }
            });
        }

        updateSpeedDisplay('base-slider', 'base-angle');
        updateSpeedDisplay('shoulder-slider', 'shoulder-angle');
        updateSpeedDisplay('elbow-slider', 'elbow-angle');
        updateSpeedDisplay('gripper-slider', 'gripper-angle');

        // Move on slider release (not during drag)
        document.getElementById('base-slider').addEventListener('change', function() {
            setAngle('base', this.value);
        });
        document.getElementById('shoulder-slider').addEventListener('change', function() {
            setAngle('shoulder', this.value);
        });
        document.getElementById('elbow-slider').addEventListener('change', function() {
            setAngle('elbow', this.value);
        });
        document.getElementById('gripper-slider').addEventListener('change', function() {
            setAngle('gripper', this.value);
        });

        function setAngle(joint, angle) {
            // Update display immediately for smooth UX
            updateAngleDisplay(joint, angle);

            fetch('/move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ joint: joint, angle: angle })
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    // Only update server values after successful move
                    window.updatingFromServer = true;
                    updateCurrentAngles(data.angles);
                    window.updatingFromServer = false;
                } else {
                    // Revert on error
                    fetch('/angles')
                    .then(response => response.json())
                    .then(currentAngles => {
                        window.updatingFromServer = true;
                        updateCurrentAngles(currentAngles);
                        window.updatingFromServer = false;
                    });
                }
            })
            .catch(error => {
                showStatus('error', 'Error de conexión: ' + error);
                // Revert on error
                fetch('/angles')
                .then(response => response.json())
                .then(currentAngles => {
                    window.updatingFromServer = true;
                    updateCurrentAngles(currentAngles);
                    window.updatingFromServer = false;
                });
            });
        }

        function updateAngleDisplay(joint, angle) {
            // Update the display immediately when slider moves
            const displayId = joint + '-angle';
            const displayElement = document.getElementById(displayId);
            if (displayElement) {
                displayElement.textContent = angle + '°';
            }
        }

        function goHome() {
            fetch('/home', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    updateCurrentAngles(data.angles);
                }
            })
            .catch(error => {
                showStatus('error', 'Error de conexión: ' + error);
            });
        }

        function testSequence() {
            fetch('/test', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    updateCurrentAngles(data.angles);
                }
            })
            .catch(error => {
                showStatus('error', 'Error de conexión: ' + error);
            });
        }

        function updateCurrentAngles(angles) {
            // Only update if we have valid angles
            if (angles && typeof angles === 'object') {
                document.getElementById('current-base').textContent = angles.base + '°';
                document.getElementById('current-shoulder').textContent = angles.shoulder + '°';
                document.getElementById('current-elbow').textContent = angles.elbow + '°';
                document.getElementById('current-gripper').textContent = angles.gripper + '°';

                // Update sliders ONLY when explicitly requested (not during drag)
                // This prevents sliders from jumping around while user is adjusting
                if (window.updatingFromServer) {
                    document.getElementById('base-slider').value = angles.base;
                    document.getElementById('shoulder-slider').value = angles.shoulder;
                    document.getElementById('elbow-slider').value = angles.elbow;
                    document.getElementById('gripper-slider').value = angles.gripper;

                    // Update angle displays
                    document.getElementById('base-angle').textContent = angles.base + '°';
                    document.getElementById('shoulder-angle').textContent = angles.shoulder + '°';
                    document.getElementById('elbow-angle').textContent = angles.elbow + '°';
                    document.getElementById('gripper-angle').textContent = angles.gripper + '°';
                }
            }
        }

        function showStatus(type, message) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';

            // Hide after 3 seconds
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }

        // Initialize updating flag
        window.updatingFromServer = false;

        // Auto-update sliders to current values (only once at startup)
        setTimeout(() => {
            fetch('/angles')
            .then(response => response.json())
            .then(data => {
                window.updatingFromServer = true;
                updateCurrentAngles(data);
                window.updatingFromServer = false;
            });
        }, 1000);

        // Nuevas funciones para configuración
        function updateSpeed(speed) {
            fetch('/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ setting: 'speed', value: parseInt(speed) })
            })
            .then(response => response.json())
            .then(data => {
                showStatus('success', 'Velocidad actualizada: ' + data.value);
            });
        }

        function updateSmoothing(steps) {
            fetch('/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ setting: 'smooth_steps', value: parseInt(steps) })
            })
            .then(response => response.json())
            .then(data => {
                showStatus('success', 'Suavizado actualizado: ' + data.value + ' pasos');
            });
        }

        function emergencyStop() {
            fetch('/emergency_stop', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                showStatus('warning', data.message);
                updateCurrentAngles(data.angles);
            });
        }

        // Prevenir movimientos demasiado rápidos
        let lastMoveTime = 0;
        const MOVE_COOLDOWN = 100; // ms

        function setAngle(joint, angle) {
            const now = Date.now();
            if (now - lastMoveTime < MOVE_COOLDOWN) {
                return; // Ignorar movimientos demasiado frecuentes
            }
            lastMoveTime = now;

            // Update display immediately for smooth UX
            updateAngleDisplay(joint, angle);

            fetch('/move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ joint: joint, angle: angle })
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    // Only update server values after successful move
                    window.updatingFromServer = true;
                    updateCurrentAngles(data.angles);
                    window.updatingFromServer = false;
                } else {
                    // Revert on error
                    fetch('/angles')
                    .then(response => response.json())
                    .then(currentAngles => {
                        window.updatingFromServer = true;
                        updateCurrentAngles(currentAngles);
                        window.updatingFromServer = false;
                    });
                }
            })
            .catch(error => {
                showStatus('error', 'Error de conexión: ' + error);
                // Revert on error
                fetch('/angles')
                .then(response => response.json())
                .then(currentAngles => {
                    window.updatingFromServer = true;
                    updateCurrentAngles(currentAngles);
                    window.updatingFromServer = false;
                });
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, angles=controlador.angulos_actuales)

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    joint = data.get('joint')
    angle = data.get('angle')

    success, message = controlador.mover_articulación(joint, angle)

    return jsonify({
        'success': success,
        'message': message,
        'angles': controlador.angulos_actuales
    })

@app.route('/home', methods=['POST'])
def home():
    success, message = controlador.ir_a_home()
    return jsonify({
        'success': success,
        'message': message,
        'angles': controlador.angulos_actuales
    })

@app.route('/test', methods=['POST'])
def test():
    success, message = controlador.secuencia_prueba()
    return jsonify({
        'success': success,
        'message': message,
        'angles': controlador.angulos_actuales
    })

@app.route('/angles')
def get_angles():
    return jsonify(controlador.angulos_actuales)

@app.route('/config', methods=['POST'])
def config():
    data = request.get_json()
    setting = data.get('setting')
    value = data.get('value')

    if setting == 'speed':
        controlador.velocidad = max(1, min(10, value))
        return jsonify({'success': True, 'value': controlador.velocidad})
    elif setting == 'smooth_steps':
        controlador.pasos_suavizado = max(5, min(30, value))
        return jsonify({'success': True, 'value': controlador.pasos_suavizado})

    return jsonify({'success': False, 'message': 'Configuración no válida'})

@app.route('/emergency_stop', methods=['POST'])
def emergency_stop():
    """Detener todos los movimientos inmediatamente"""
    try:
        # Mover a posición segura
        controlador.controlador_robot.mover_base(180, velocidad=1)
        controlador.controlador_robot.mover_hombro(45, velocidad=1)
        controlador.controlador_robot.mover_codo(90, velocidad=1)
        controlador.controlador_robot.mover_pinza(0, velocidad=1)

        controlador.angulos_actuales = {'base': 180, 'shoulder': 45, 'elbow': 90, 'gripper': 0}
        return jsonify({
            'success': True,
            'message': 'Parada de emergencia ejecutada',
            'angles': controlador.angulos_actuales
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error en parada de emergencia: {e}'
        })

if __name__ == '__main__':
    print("🤖 Iniciando servidor web en http://localhost:5000")
    print("Asegúrate de que la alimentación del brazo esté CONECTADA")
    app.run(host='0.0.0.0', port=5000, debug=False)