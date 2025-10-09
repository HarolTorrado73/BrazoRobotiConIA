#!/usr/bin/env python3
"""
Lógica de movimientos del brazo robótico
Incluye cinemática directa/inversa básica y movimientos predefinidos
"""

import math
import time
import logging
import json
import os
from servo_controller import ServoController
from stepper_motor import StepperMotor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobotArm:
    def __init__(self, servo_controller=None, stepper_motor=None):
        """
        Inicializa el brazo robótico
        """
        self.servo_controller = servo_controller or ServoController()
        self.stepper_motor = stepper_motor or StepperMotor()

        # Archivo de calibración
        self.calibration_file = "calibration_data.json"
        self.calibration_data = self.load_calibration_data()

        # Dimensiones del brazo (en mm, usar datos calibrados si disponibles)
        self.link_lengths = self.calibration_data.get('arm_dimensions', {
            'base_height': 50,    # Altura de la base
            'upper_arm': 200,     # Longitud brazo superior
            'forearm': 150,       # Longitud antebrazo
            'gripper_offset': 50  # Offset de la pinza
        })

        # Límites de trabajo (ajustar según calibración)
        self.workspace_limits = {
            'x': (-300, 300),    # mm
            'y': (0, 400),       # mm
            'z': (0, 350)        # mm
        }

        # Posición actual (x, y, z) en mm
        self.current_position = (200, 0, 150)

        logger.info("RobotArm inicializado con datos de calibración")

    def load_calibration_data(self):
        """
        Carga datos de calibración desde archivo
        """
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando calibración: {e}")

        # Valores por defecto
        return {
            'servo_offsets': {'base': 0, 'shoulder': 0, 'elbow': 0, 'gripper': 0},
            'arm_dimensions': {
                'base_height': 50,
                'upper_arm': 200,
                'forearm': 150,
                'gripper_offset': 50
            }
        }

    def move_to_position(self, x, y, z, speed='normal'):
        """
        Mueve el brazo a una posición 3D específica
        Args:
            x, y, z: Coordenadas en mm
            speed: 'slow', 'normal', 'fast'
        """
        # Verificar límites
        if not (self.workspace_limits['x'][0] <= x <= self.workspace_limits['x'][1] and
                self.workspace_limits['y'][0] <= y <= self.workspace_limits['y'][1] and
                self.workspace_limits['z'][0] <= z <= self.workspace_limits['z'][1]):
            logger.warning(f"Posición {x, y, z} fuera de límites de trabajo")
            return False

        # Aplicar correcciones de posición si existen
        corrected_pos = self.apply_position_corrections(x, y, z)
        x, y, z = corrected_pos

        # Calcular ángulos usando cinemática inversa
        angles = self.inverse_kinematics(x, y, z)
        if angles is None:
            logger.error("No se pudo calcular la cinemática inversa")
            return False

        # Aplicar velocidades
        delays = {'slow': 0.2, 'normal': 0.1, 'fast': 0.05}
        delay = delays.get(speed, 0.1)

        # Mover servos
        angle_dict = {
            'base': angles['base'],
            'shoulder': angles['shoulder'],
            'elbow': angles['elbow']
        }

        self.servo_controller.move_all(angle_dict, delay)
        self.current_position = (x, y, z)

        logger.info(f"Brazo movido a posición ({x}, {y}, {z})")
        return True

    def inverse_kinematics(self, x, y, z):
        """
        Calcula los ángulos de los servos para una posición 3D
        Retorna diccionario con ángulos o None si no es posible
        """
        # Coordenadas en plano XY (ignorando rotación base por ahora)
        r = math.sqrt(x**2 + y**2)

        # Altura efectiva
        z_eff = z - self.link_lengths['base_height']

        # Longitudes de los eslabones
        L1 = self.link_lengths['upper_arm']
        L2 = self.link_lengths['forearm']

        # Distancia al punto objetivo
        d = math.sqrt(r**2 + z_eff**2)

        # Verificar alcance
        if d > (L1 + L2) or d < abs(L1 - L2):
            return None

        # Ángulo del codo (ley de cosenos)
        cos_elbow = (L1**2 + L2**2 - d**2) / (2 * L1 * L2)
        elbow_angle = math.acos(max(-1, min(1, cos_elbow)))

        # Ángulo del hombro
        k1 = L1 + L2 * math.cos(elbow_angle)
        k2 = L2 * math.sin(elbow_angle)
        shoulder_angle = math.atan2(z_eff, r) + math.atan2(k2, k1)

        # Ángulo de la base (rotación)
        base_angle = math.atan2(y, x)

        # Convertir a grados y ajustar offsets calibrados
        servo_offsets = self.calibration_data.get('servo_offsets', {'base': 0, 'shoulder': 0, 'elbow': 0})
        angles = {
            'base': math.degrees(base_angle) + servo_offsets.get('base', 90),
            'shoulder': math.degrees(shoulder_angle) + servo_offsets.get('shoulder', 90),
            'elbow': math.degrees(elbow_angle) + servo_offsets.get('elbow', 0)
        }

        # Verificar límites de servos
        limits = self.servo_controller.limits
        for servo, angle in angles.items():
            if servo in limits:
                min_angle, max_angle = limits[servo]
                if not (min_angle <= angle <= max_angle):
                    logger.warning(f"Ángulo {angle} para {servo} fuera de límites")
                    return None

        return angles

    def forward_kinematics(self, base_angle, shoulder_angle, elbow_angle):
        """
        Calcula la posición 3D a partir de los ángulos de los servos
        """
        # Aplicar offsets inversos para obtener ángulos reales
        servo_offsets = self.calibration_data.get('servo_offsets', {'base': 0, 'shoulder': 0, 'elbow': 0})
        base_real = base_angle - servo_offsets.get('base', 90)
        shoulder_real = shoulder_angle - servo_offsets.get('shoulder', 90)
        elbow_real = elbow_angle - servo_offsets.get('elbow', 0)

        # Convertir a radianes
        base_rad = math.radians(base_real)
        shoulder_rad = math.radians(shoulder_real)
        elbow_rad = math.radians(elbow_real)

        L1 = self.link_lengths['upper_arm']
        L2 = self.link_lengths['forearm']

        # Posición del codo
        elbow_x = L1 * math.cos(shoulder_rad)
        elbow_z = L1 * math.sin(shoulder_rad)

        # Posición del extremo
        end_x = elbow_x + L2 * math.cos(shoulder_rad + elbow_rad)
        end_z = elbow_z + L2 * math.sin(shoulder_rad + elbow_rad)

        # Aplicar rotación de la base
        x = end_x * math.cos(base_rad)
        y = end_x * math.sin(base_rad)
        z = end_z + self.link_lengths['base_height']

        return (x, y, z)

    def pick_and_place(self, pick_pos, place_pos, speed='normal'):
        """
        Movimiento de recoger y colocar
        Args:
            pick_pos: (x, y, z) posición de recogida
            place_pos: (x, y, z) posición de colocación
        """
        logger.info("Iniciando secuencia pick and place")

        # Ir a posición segura
        self.move_to_position(200, 0, 200, speed)

        # Ir a posición de recogida
        pick_x, pick_y, pick_z = pick_pos
        self.move_to_position(pick_x, pick_y, pick_z + 50, speed)  # 50mm arriba
        self.move_to_position(pick_x, pick_y, pick_z, speed)

        # Cerrar pinza
        self.servo_controller.close_gripper()
        time.sleep(1)

        # Levantar objeto
        self.move_to_position(pick_x, pick_y, pick_z + 50, speed)

        # Ir a posición de colocación
        place_x, place_y, place_z = place_pos
        self.move_to_position(place_x, place_y, place_z + 50, speed)
        self.move_to_position(place_x, place_y, place_z, speed)

        # Abrir pinza
        self.servo_controller.open_gripper()
        time.sleep(1)

        # Retirarse
        self.move_to_position(place_x, place_y, place_z + 50, speed)

        # Volver a posición segura
        self.move_to_position(200, 0, 200, speed)

        logger.info("Secuencia pick and place completada")

    def scan_area(self, center_x, center_y, width, height, steps=5):
        """
        Escanea un área rectangular
        """
        logger.info(f"Escaneando área alrededor de ({center_x}, {center_y})")

        z_scan = 150  # Altura de escaneo
        step_x = width / (steps - 1) if steps > 1 else 0
        step_y = height / (steps - 1) if steps > 1 else 0

        for i in range(steps):
            for j in range(steps):
                x = center_x - width/2 + i * step_x
                y = center_y - height/2 + j * step_y

                if self.move_to_position(x, y, z_scan, 'slow'):
                    time.sleep(0.5)  # Pausa para observación

        logger.info("Escaneo completado")

    def follow_object(self, vision_system, object_label, max_distance=300):
        """
        Sigue un objeto detectado por el sistema de visión
        """
        logger.info(f"Iniciando seguimiento de objeto: {object_label}")

        vision_system.set_target_object(object_label)

        while True:
            target_pos = vision_system.get_target_position()
            if target_pos:
                x, y, w, h = target_pos
                # Convertir coordenadas de imagen a mundo real (calibración necesaria)
                world_x = (x - 320) * 0.5  # Ejemplo de conversión simple
                world_y = 200  # Distancia fija hacia adelante
                world_z = 150

                # Limitar distancia
                distance = math.sqrt(world_x**2 + world_y**2)
                if distance > max_distance:
                    scale = max_distance / distance
                    world_x *= scale
                    world_y *= scale

                self.move_to_position(world_x, world_y, world_z, 'slow')
                time.sleep(0.1)
            else:
                time.sleep(0.5)

    def draw_circle(self, center_x, center_y, radius, height, steps=36):
        """
        Dibuja un círculo con el brazo
        """
        logger.info(f"Dibujando círculo en ({center_x}, {center_y}) radio {radius}")

        for i in range(steps):
            angle = 2 * math.pi * i / steps
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            z = height

            self.move_to_position(x, y, z, 'fast')

        logger.info("Círculo dibujado")

    def home_position(self):
        """
        Mueve el brazo a posición inicial
        """
        self.servo_controller.home_position()
        self.stepper_motor.home()
        self.current_position = (200, 0, 150)
        logger.info("Brazo en posición inicial")

    def get_position(self):
        """
        Retorna la posición actual
        """
        return self.current_position

    def calibrate(self):
        """
        Rutina de calibración mejorada con ajuste de offsets
        """
        logger.info("Iniciando calibración avanzada...")

        # Recargar datos de calibración
        self.calibration_data = self.load_calibration_data()

        # Aquí se podría implementar calibración automática usando visión
        # Por ahora, actualizar dimensiones si han cambiado
        self.link_lengths = self.calibration_data.get('arm_dimensions', self.link_lengths)

        self.home_position()
        logger.info("Calibración completada con datos actualizados")

    def reload_calibration(self):
        """
        Recarga datos de calibración desde archivo
        """
        self.calibration_data = self.load_calibration_data()
        self.link_lengths = self.calibration_data.get('arm_dimensions', self.link_lengths)
        logger.info("Datos de calibración recargados")

    def apply_position_corrections(self, x, y, z):
        """
        Aplica correcciones de posición basadas en datos de calibración
        """
        corrections = self.calibration_data.get('position_corrections', {})

        # Buscar corrección más cercana (por ahora, exacta)
        pos_key = f"{int(x)},{int(y)},{int(z)}"
        if pos_key in corrections:
            corr_x, corr_y, corr_z = corrections[pos_key]
            corrected_x = x + corr_x
            corrected_y = y + corr_y
            corrected_z = z + corr_z
            logger.debug(f"Corrección aplicada a {pos_key}: ({corr_x}, {corr_y}, {corr_z})")
            return (corrected_x, corrected_y, corrected_z)

        return (x, y, z)

    def learn_position_correction(self, target_pos, actual_pos):
        """
        Aprende corrección de posición basada en error observado
        Args:
            target_pos: (x, y, z) posición objetivo
            actual_pos: (x, y, z) posición real medida
        """
        if 'position_corrections' not in self.calibration_data:
            self.calibration_data['position_corrections'] = {}

        tx, ty, tz = target_pos
        ax, ay, az = actual_pos

        # Calcular error
        error_x = ax - tx
        error_y = ay - ty
        error_z = az - tz

        # Almacenar corrección (negativa del error)
        pos_key = f"{int(tx)},{int(ty)},{int(tz)}"
        self.calibration_data['position_corrections'][pos_key] = (-error_x, -error_y, -error_z)

        logger.info(f"Corrección aprendida para {pos_key}: ({-error_x}, {-error_y}, {-error_z})")

        # Guardar en archivo
        self.save_calibration_data()

    def save_calibration_data(self):
        """
        Guarda datos de calibración en archivo
        """
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump(self.calibration_data, f, indent=4)
            logger.info("Datos de calibración guardados")
        except Exception as e:
            logger.error(f"Error guardando calibración: {e}")

if __name__ == "__main__":
    # Prueba del brazo robótico
    arm = RobotArm()
    try:
        arm.home_position()
        time.sleep(2)

        # Movimiento de prueba
        arm.move_to_position(150, 100, 100)
        time.sleep(2)

        # Dibujar un pequeño círculo
        arm.draw_circle(150, 100, 50, 100)

        arm.home_position()

    except KeyboardInterrupt:
        pass
    finally:
        arm.servo_controller.cleanup()
        arm.stepper_motor.cleanup()