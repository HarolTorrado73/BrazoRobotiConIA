import time
import board
import busio
from adafruit_pca9685 import PCA9685
from gpiozero import OutputDevice
import logging as log

class ControladorServo:
    """Controlador para servos continuos usando PCA9685"""

    def __init__(self, direccion_i2c=0x40, frecuencia=50):
        """Inicializar controlador PCA9685"""
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(self.i2c, address=direccion_i2c)
        self.pca.frequency = frecuencia
        self.servos = {}

    def agregar_servo(self, nombre, canal, pulso_min=500, pulso_max=2500, angulo_min=0, angulo_max=180):
        """Agregar servo al controlador"""
        # Usar rango completo de pulso para servos MG996R
        self.servos[nombre] = {
            'canal': canal,
            'pulso_min': pulso_min,
            'pulso_max': pulso_max,
            'angulo_min': angulo_min,
            'angulo_max': angulo_max
        }

    def establecer_angulo(self, nombre, angulo, velocidad=1.0):
        """Establecer velocidad del servo continuo"""
        if nombre not in self.servos:
            log.error(f"Servo {nombre} no configurado")
            return

        servo = self.servos[nombre]
        angulo = max(servo['angulo_min'], min(servo['angulo_max'], angulo))

        # CONTROL DE SERVOS CONTINUOS - Control de velocidad, no posición
        # Mapear ángulo a velocidad: 180° = parar, <180° = giro horario, >180° = giro antihorario
        if angulo == 180:
            # Detener
            pulso = 1500
        elif angulo < 180:
            # Giro horario (180° a 0° = rápido a lento)
            factor_velocidad = (180 - angulo) / 180.0  # 0 a 1
            pulso = 1500 + (500 * factor_velocidad)  # 1500-2000us
        else:
            # Giro antihorario (180° a 360° = rápido a lento)
            factor_velocidad = (angulo - 180) / 180.0  # 0 a 1
            pulso = 1500 - (500 * factor_velocidad)  # 1500-1000us

        ciclo_trabajo = int(pulso / 20000 * 0xFFFF)  # Periodo 50Hz
        self.pca.channels[servo['canal']].duty_cycle = ciclo_trabajo

        # Retardo mínimo para control responsivo
        time.sleep(0.02 / velocidad)

class ControladorStepper:
    """Controlador para motores stepper"""

    def __init__(self, pin_paso, pin_direccion, pin_habilitar=None, pasos_por_rev=200, micropasos=16):
        """Inicializar controlador stepper"""
        self.pin_paso = OutputDevice(pin_paso)
        self.pin_direccion = OutputDevice(pin_direccion)
        self.pin_habilitar = OutputDevice(pin_habilitar) if pin_habilitar else None
        self.pasos_por_rev = pasos_por_rev * micropasos
        self.posicion_actual = 0

    def habilitar(self):
        """Habilitar motor stepper"""
        if self.pin_habilitar:
            self.pin_habilitar.off()  # Asumiendo activo bajo

    def deshabilitar(self):
        """Deshabilitar motor stepper"""
        if self.pin_habilitar:
            self.pin_habilitar.on()

    def mover_pasos(self, pasos, direccion=1, velocidad=1000):  # pasos por segundo
        """Mover stepper una cantidad específica de pasos"""
        self.pin_direccion.value = 1 if direccion > 0 else 0
        retardo = 1.0 / velocidad
        for _ in range(abs(pasos)):
            self.pin_paso.on()
            time.sleep(retardo / 2)
            self.pin_paso.off()
            time.sleep(retardo / 2)
        self.posicion_actual += pasos * direccion

    def mover_distancia(self, distancia_mm, paso_tuerca=8, direccion=1, velocidad=1000):
        """Mover stepper una distancia específica en mm"""
        pasos = int((distancia_mm / paso_tuerca) * self.pasos_por_rev)
        self.mover_pasos(pasos, direccion, velocidad)

class ControladorRobotico:
    """Controlador principal del brazo robótico"""

    def __init__(self):
        """Inicializar controlador del robot"""
        self.controlador_servo = ControladorServo()
        # Configurar servos: base (canal 0), hombro (1), codo (2), pinza (3)
        # Todos los servos son continuos de 360°
        self.controlador_servo.agregar_servo('base', 0, angulo_min=0, angulo_max=360)
        self.controlador_servo.agregar_servo('shoulder', 1, angulo_min=0, angulo_max=360)
        self.controlador_servo.agregar_servo('elbow', 2, angulo_min=0, angulo_max=360)
        self.controlador_servo.agregar_servo('gripper', 3, angulo_min=0, angulo_max=360)

        # Stepper para elevación del brazo: paso=17, dir=18, hab=19 (pines BCM)
        self.controlador_stepper = ControladorStepper(pin_paso=17, pin_direccion=18, pin_habilitar=19)

    def mover_base(self, angulo, velocidad=5):
        """Mover base del robot"""
        self.controlador_servo.establecer_angulo('base', angulo, velocidad)

    def mover_hombro(self, angulo, velocidad=5):
        """Mover hombro del robot"""
        self.controlador_servo.establecer_angulo('shoulder', angulo, velocidad)

    def mover_codo(self, angulo, velocidad=5):
        """Mover codo del robot"""
        self.controlador_servo.establecer_angulo('elbow', angulo, velocidad)

    def mover_pinza(self, angulo, velocidad=5):
        """Mover pinza del robot"""
        self.controlador_servo.establecer_angulo('gripper', angulo, velocidad)

    def mover_brazo(self, distancia_mm, direccion=1, velocidad=1000):
        """Mover brazo stepper una distancia específica"""
        self.controlador_stepper.mover_distancia(distancia_mm, direccion=direccion, velocidad=velocidad)

    def accion_recoger(self):
        """Abrir pinza para recoger"""
        self.mover_pinza(90)  # Abrir

    def accion_soltar(self):
        """Cerrar pinza para soltar"""
        self.mover_pinza(270)  # Cerrar

    def accion_subir(self, distancia=50):
        """Subir brazo stepper"""
        self.mover_brazo(distancia, direccion=1)

    def cerrar(self):
        """Cerrar controladores y liberar recursos"""
        self.controlador_stepper.deshabilitar()
        self.controlador_servo.pca.deinit()
