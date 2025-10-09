#!/usr/bin/env python3
"""
Controlador de servos usando PCA9685
Compatible con Raspberry Pi 5 y servos MG996R
"""

import time
import logging
import math
from adafruit_servokit import ServoKit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServoController:
    def __init__(self, channels=16, address=0x40, frequency=50):
        """
        Inicializa el controlador PCA9685
        Args:
            channels: Número de canales (16 para PCA9685)
            address: Dirección I2C del PCA9685
            frequency: Frecuencia PWM en Hz (50Hz para servos)
        """
        try:
            self.kit = ServoKit(channels=channels, address=address)
            self.kit.frequency = frequency
            self.channels = channels

            # Configuración específica para servos MG996R
            self.limits = {
                'base': (0, 180),      # Rango de movimiento en grados
                'shoulder': (0, 180),
                'elbow': (0, 180),
                'gripper': (0, 180)
            }

            # Mapeo de servos a canales PCA9685
            self.servo_channels = {
                'base': 0,
                'shoulder': 1,
                'elbow': 2,
                'gripper': 3
            }

            # Configurar rangos de pulso para MG996R (aprox)
            for servo_name, channel in self.servo_channels.items():
                self.kit.servo[channel].set_pulse_width_range(500, 2500)  # 0.5ms - 2.5ms

            logger.info(f"ServoController inicializado con PCA9685 en dirección 0x{address:02X}")

        except Exception as e:
            logger.error(f"Error inicializando PCA9685: {e}")
            raise

    def set_angle(self, servo_name, angle):
        """
        Establece el ángulo de un servo específico
        Args:
            servo_name: 'base', 'shoulder', 'elbow', 'gripper'
            angle: Ángulo en grados (0-180)
        """
        if servo_name not in self.servo_channels:
            logger.error(f"Servo {servo_name} no encontrado")
            return False

        # Verificar límites
        min_angle, max_angle = self.limits.get(servo_name, (0, 180))
        angle = max(min_angle, min(max_angle, angle))

        channel = self.servo_channels[servo_name]

        try:
            self.kit.servo[channel].angle = angle
            logger.debug(f"Servo {servo_name} movido a {angle}°")
            return True
        except Exception as e:
            logger.error(f"Error moviendo servo {servo_name}: {e}")
            return False

    def get_angle(self, servo_name):
        """
        Obtiene el ángulo actual de un servo
        Nota: PCA9685 no puede leer posición, retorna último valor establecido
        """
        # Como PCA9685 es solo salida, no podemos leer posición real
        # En una implementación real necesitaríamos potenciómetros o encoders
        logger.warning("PCA9685 no puede leer posición de servos")
        return None

    def move_all(self, angle_dict, delay=0.1):
        """
        Mueve múltiples servos simultáneamente
        Args:
            angle_dict: Diccionario {'servo_name': angle}
            delay: Retardo entre movimientos en segundos
        """
        for servo_name, angle in angle_dict.items():
            self.set_angle(servo_name, angle)
            if delay > 0:
                time.sleep(delay)

    def home_position(self):
        """
        Mueve todos los servos a posición inicial (90°)
        """
        home_angles = {
            'base': 90,
            'shoulder': 90,
            'elbow': 90,
            'gripper': 90
        }
        self.move_all(home_angles, 0.2)
        logger.info("Servos en posición inicial")

    def open_gripper(self, angle=180):
        """
        Abre la pinza
        """
        self.set_angle('gripper', angle)
        logger.info("Pinza abierta")

    def close_gripper(self, angle=0):
        """
        Cierra la pinza
        """
        self.set_angle('gripper', angle)
        logger.info("Pinza cerrada")

    def test_servos(self):
        """
        Prueba funcional de todos los servos
        """
        logger.info("Probando servos...")

        try:
            # Mover cada servo de 0° a 180° y viceversa
            for servo_name in self.servo_channels.keys():
                logger.info(f"Probando {servo_name}")

                # 0°
                self.set_angle(servo_name, 0)
                time.sleep(1)

                # 90°
                self.set_angle(servo_name, 90)
                time.sleep(1)

                # 180°
                self.set_angle(servo_name, 180)
                time.sleep(1)

                # Volver a 90°
                self.set_angle(servo_name, 90)
                time.sleep(1)

            logger.info("Prueba de servos completada exitosamente")
            return True

        except Exception as e:
            logger.error(f"Error en prueba de servos: {e}")
            return False

    def cleanup(self):
        """
        Limpia recursos
        """
        try:
            # No hay cleanup específico para PCA9685
            logger.info("ServoController limpiado")
        except Exception as e:
            logger.error(f"Error en cleanup: {e}")

if __name__ == "__main__":
    # Prueba del controlador de servos
    controller = ServoController()
    try:
        controller.test_servos()
    finally:
        controller.cleanup()