#!/usr/bin/env python3
"""
Controlador de motor paso a paso NEMA 17 usando TMC2209
Compatible con Raspberry Pi 5
"""

import time
import logging
import RPi.GPIO as GPIO
from TMC2209 import TMC2209

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StepperMotor:
    def __init__(self, en_pin=22, dir_pin=23, step_pin=24, uart_port="/dev/serial0"):
        """
        Inicializa el controlador TMC2209 para motor NEMA 17
        Args:
            en_pin: Pin GPIO para enable
            dir_pin: Pin GPIO para dirección
            step_pin: Pin GPIO para step
            uart_port: Puerto UART para comunicación con TMC2209
        """
        # Configurar GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(en_pin, GPIO.OUT)
        GPIO.setup(dir_pin, GPIO.OUT)
        GPIO.setup(step_pin, GPIO.OUT)

        self.en_pin = en_pin
        self.dir_pin = dir_pin
        self.step_pin = step_pin

        # Inicializar TMC2209
        try:
            self.driver = TMC2209(
                0,  # Dirección por defecto
                serialport=uart_port,
                baudrate=115200
            )

            # Configurar driver
            self.driver.setCurrent(800)  # Corriente en mA (ajustar según motor)
            self.driver.setMicrosteps(16)  # Microstepping 1/16
            self.driver.setEnabled(True)

            # Configuración para NEMA 17
            self.steps_per_revolution = 200  # Pasos por vuelta del motor
            self.microsteps = 16
            self.steps_per_revolution_micro = self.steps_per_revolution * self.microsteps

            # Estado del motor
            self.current_position = 0  # Posición actual en pasos
            self.max_speed = 1000  # Velocidad máxima en pasos/segundo

            # Deshabilitar motor inicialmente
            GPIO.output(self.en_pin, GPIO.HIGH)

            logger.info("StepperMotor inicializado con TMC2209")

        except Exception as e:
            logger.error(f"Error inicializando TMC2208: {e}")
            raise

    def enable_motor(self):
        """Habilita el motor"""
        GPIO.output(self.en_pin, GPIO.LOW)
        self.driver.setEnabled(True)
        logger.debug("Motor habilitado")

    def disable_motor(self):
        """Deshabilita el motor"""
        GPIO.output(self.en_pin, GPIO.HIGH)
        self.driver.setEnabled(False)
        logger.debug("Motor deshabilitado")

    def set_direction(self, clockwise=True):
        """
        Establece la dirección del motor
        Args:
            clockwise: True para sentido horario, False para antihorario
        """
        GPIO.output(self.dir_pin, GPIO.HIGH if clockwise else GPIO.LOW)

    def step(self, steps=1, delay=0.001):
        """
        Realiza un número específico de pasos
        Args:
            steps: Número de pasos
            delay: Retardo entre pasos en segundos
        """
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(delay)

    def move_steps(self, steps, speed=500):
        """
        Mueve el motor un número específico de pasos
        Args:
            steps: Número de pasos (positivo = CW, negativo = CCW)
            speed: Velocidad en pasos por segundo
        """
        if steps == 0:
            return

        # Determinar dirección
        direction = steps > 0
        steps = abs(steps)

        self.enable_motor()
        self.set_direction(direction)

        # Calcular delay basado en velocidad
        delay = 1.0 / speed if speed > 0 else 0.001
        delay = max(0.0001, delay)  # Mínimo delay

        logger.debug(f"Moviendo {steps} pasos a {speed} pasos/seg (delay: {delay:.6f}s)")

        # Ejecutar pasos
        self.step(steps, delay)

        # Actualizar posición
        self.current_position += steps if direction else -steps

        self.disable_motor()

    def move_degrees(self, degrees, speed=500):
        """
        Mueve el motor un ángulo específico
        Args:
            degrees: Ángulo en grados
            speed: Velocidad en pasos por segundo
        """
        steps = int((degrees / 360.0) * self.steps_per_revolution_micro)
        self.move_steps(steps, speed)

    def move_revolutions(self, revolutions, speed=500):
        """
        Mueve el motor un número específico de vueltas
        Args:
            revolutions: Número de vueltas
            speed: Velocidad en pasos por segundo
        """
        steps = int(revolutions * self.steps_per_revolution_micro)
        self.move_steps(steps, speed)

    def home(self):
        """
        Mueve el motor a posición inicial (home)
        Nota: Requiere sensor de fin de carrera para implementación real
        """
        logger.info("Moviendo a posición home")
        # En implementación real, buscar fin de carrera
        # Por ahora, solo resetear posición
        self.current_position = 0
        logger.info("Motor en posición home")

    def get_position(self):
        """
        Retorna la posición actual en pasos
        """
        return self.current_position

    def get_position_degrees(self):
        """
        Retorna la posición actual en grados
        """
        return (self.current_position / self.steps_per_revolution_micro) * 360.0

    def set_position(self, position):
        """
        Establece la posición actual (para calibración)
        """
        self.current_position = position
        logger.debug(f"Posición establecida a {position} pasos")

    def test_motor(self):
        """
        Prueba funcional del motor
        """
        logger.info("Probando motor paso a paso...")

        try:
            # Habilitar motor
            self.enable_motor()
            time.sleep(0.1)

            # Movimiento de prueba: 1 vuelta en cada dirección
            logger.info("Moviendo 1 vuelta CW")
            self.move_revolutions(1, 200)
            time.sleep(1)

            logger.info("Moviendo 1 vuelta CCW")
            self.move_revolutions(-1, 200)
            time.sleep(1)

            # Volver a home
            self.home()

            logger.info("Prueba de motor completada exitosamente")
            return True

        except Exception as e:
            logger.error(f"Error en prueba de motor: {e}")
            return False
        finally:
            self.disable_motor()

    def cleanup(self):
        """
        Limpia recursos GPIO
        """
        try:
            self.disable_motor()
            GPIO.cleanup()
            logger.info("StepperMotor limpiado")
        except Exception as e:
            logger.error(f"Error en cleanup: {e}")

if __name__ == "__main__":
    # Prueba del motor paso a paso
    motor = StepperMotor()
    try:
        motor.test_motor()
    finally:
        motor.cleanup()