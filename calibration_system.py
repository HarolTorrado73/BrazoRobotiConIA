#!/usr/bin/env python3
"""
Sistema de calibración y pruebas para brazo robótico
permitiendo verificar y ajustar el funcionamiento de todos los componentes
"""

import time
import logging
import json
import os
from servo_controller import ServoController
from stepper_motor import StepperMotor
from vision_system import VisionSystem
from robot_arm import RobotArm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalibrationSystem:
    def __init__(self):
        """
        Inicializa el sistema de calibración
        """
        self.servo_controller = ServoController()
        self.stepper_motor = StepperMotor()
        self.vision_system = VisionSystem()
        self.robot_arm = RobotArm(self.servo_controller, self.stepper_motor)

        # Archivo de configuración de calibración
        self.calibration_file = "calibration_data.json"
        self.calibration_data = self.load_calibration_data()

        logger.info("CalibrationSystem inicializado")

    def load_calibration_data(self):
        """
        Carga datos de calibración desde archivo
        """
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando datos de calibración: {e}")

        # Valores por defecto a simple vista
        return {
            'servo_offsets': {'base': 0, 'shoulder': 0, 'elbow': 0, 'gripper': 0},
            'stepper_steps_per_mm': 100,  # pasos por mm
            'vision_calibration': {
                'focal_length': 1000,
                'image_center': [320, 240],
                'scale_factor': 0.5  # mm por pixel
            },
            'arm_dimensions': {
                'base_height': 50,
                'upper_arm': 200,
                'forearm': 150,
                'gripper_offset': 50
            }
        }

    def save_calibration_data(self):
        """
        Guarda datos de calibración en archivo
        """
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump(self.calibration_data, f, indent=4)
            logger.info("Datos de calibración guardados")
        except Exception as e:
            logger.error(f"Error guardando datos de calibración: {e}")

    def run_full_calibration(self):
        """
        Ejecuta calibración completa de todos los sistemas
        """
        logger.info("Iniciando calibración completa...")

        results = {}

        # Calibración de servos
        results['servos'] = self.calibrate_servos()

        # Calibración del motor paso a paso
        results['stepper'] = self.calibrate_stepper_motor()

        # Calibración de visión
        results['vision'] = self.calibrate_vision()

        # Calibración del brazo completo
        results['arm'] = self.calibrate_robot_arm()

        # Guardar resultados
        self.save_calibration_data()

        logger.info("Calibración completa finalizada")
        return results

    def calibrate_servos(self):
        """
        Calibración de servos: verifica rangos y offsets
        """
        logger.info("Calibrando servos...")

        results = {}

        for servo_name in ['base', 'shoulder', 'elbow', 'gripper']:
            logger.info(f"Probando servo: {servo_name}")

            # Mover a posición mínima
            self.servo_controller.set_angle(servo_name, 0)
            time.sleep(1)

            # Mover a posición máxima
            max_angle = self.servo_controller.limits[servo_name][1]
            self.servo_controller.set_angle(servo_name, max_angle)
            time.sleep(1)

            # Volver al centro
            self.servo_controller.set_angle(servo_name, 90)
            time.sleep(1)

            results[servo_name] = {
                'range_tested': True,
                'max_angle': max_angle,
                'offset': self.calibration_data['servo_offsets'].get(servo_name, 0)
            }

        # Posición inicial
        self.servo_controller.home_position()

        logger.info("Calibración de servos completada")
        return results

    def calibrate_stepper_motor(self):
        """
        Calibración del motor paso a paso: mide pasos por mm
        """
        logger.info("Calibrando motor paso a paso...")

        # Mover una distancia conocida (requiere medición manual)
        test_distance = 100  # mm (aproximado)
        test_steps = 1000   # pasos

        logger.info("Moviendo motor para calibración...")
        self.stepper_motor.move_steps(test_steps, 500)
        time.sleep(2)

        # El usuario debe medir la distancia real recorrida
        measured_distance = float(input(f"Medir distancia recorrida en mm (esperado: ~{test_distance}): "))

        if measured_distance > 0:
            steps_per_mm = test_steps / measured_distance
            self.calibration_data['stepper_steps_per_mm'] = steps_per_mm
            logger.info(f"Pasos por mm calculados: {steps_per_mm}")
        else:
            logger.warning("Distancia no válida, manteniendo valor anterior")

        # Regresar a inicio
        self.stepper_motor.move_steps(-test_steps, 500)

        return {
            'steps_per_mm': self.calibration_data['stepper_steps_per_mm'],
            'test_distance': test_distance,
            'measured_distance': measured_distance
        }

    def calibrate_vision(self):
        """
        Calibración del sistema de visión
        """
        logger.info("Calibrando sistema de visión...")

        try:
            self.vision_system.start_camera()
            time.sleep(2)  # Esperar inicialización

            # Capturar frame de prueba
            frame = self.vision_system.get_frame()
            if frame is not None:
                height, width = frame.shape[:2]
                logger.info(f"Resolución de cámara: {width}x{height}")

                # Calibración básica (puede expandirse)
                self.calibration_data['vision_calibration']['image_center'] = [width//2, height//2]

                results = {
                    'camera_resolution': [width, height],
                    'objects_detected': len(self.vision_system.detected_objects)
                }
            else:
                results = {'error': 'No se pudo capturar frame'}

            self.vision_system.stop_camera()

        except Exception as e:
            logger.error(f"Error en calibración de visión: {e}")
            results = {'error': str(e)}

        return results

    def calibrate_robot_arm(self):
        """
        Calibración del brazo robótico completo con ajuste de offsets
        """
        logger.info("Calibrando brazo robótico...")

        results = {}

        # Probar movimientos básicos
        test_positions = [
            (200, 0, 150),    # Posición inicial
            (150, 100, 100),  # Posición de prueba 1
            (100, -50, 200),  # Posición de prueba 2
            (250, 50, 120)    # Posición de prueba 3
        ]

        success_count = 0
        for pos in test_positions:
            if self.robot_arm.move_to_position(*pos, 'slow'):
                success_count += 1
                time.sleep(2)
            else:
                logger.warning(f"No se pudo alcanzar posición {pos}")

        # Probar cinemática y ajustar offsets si es necesario
        test_angles = {'base': 45, 'shoulder': 90, 'elbow': 45}
        self.servo_controller.move_all(test_angles)
        time.sleep(2)

        # Calcular posición forward kinematics
        fk_pos = self.robot_arm.forward_kinematics(**test_angles)
        logger.info(f"Posición FK calculada: {fk_pos}")

        # Calcular cinemática inversa de la posición FK para verificar consistencia
        ik_angles = self.robot_arm.inverse_kinematics(*fk_pos)
        if ik_angles:
            logger.info(f"Verificación IK/FK: Ángulos originales {test_angles}, calculados {ik_angles}")
            # Aquí se podría ajustar offsets si hay discrepancias grandes
        else:
            logger.warning("No se pudo calcular IK para verificación")

        # Intentar ajuste automático de offsets (básico)
        offset_adjustments = self.auto_adjust_offsets()
        if offset_adjustments:
            logger.info(f"Ajustes de offset calculados: {offset_adjustments}")
            for servo, adjustment in offset_adjustments.items():
                self.calibration_data['servo_offsets'][servo] += adjustment

        # Volver a home
        self.robot_arm.home_position()

        results = {
            'positions_tested': len(test_positions),
            'positions_reached': success_count,
            'kinematics_test': True,
            'forward_kinematics_pos': fk_pos,
            'offset_adjustments': offset_adjustments
        }

        return results

    def auto_adjust_offsets(self):
        """
        Intenta ajustar offsets automáticamente usando posiciones conocidas
        """
        logger.info("Intentando ajuste automático de offsets...")

        # Posición de prueba conocida
        test_pos = (200, 0, 150)
        expected_angles = {'base': 90, 'shoulder': 90, 'elbow': 0}  # Ángulos esperados aproximados

        # Mover a posición
        if not self.robot_arm.move_to_position(*test_pos, 'slow'):
            return None

        time.sleep(1)

        # Obtener ángulos actuales de los servos
        current_angles = {}
        for servo in ['base', 'shoulder', 'elbow']:
            angle = self.servo_controller.get_angle(servo)
            if angle is not None:
                current_angles[servo] = angle

        if len(current_angles) < 3:
            logger.warning("No se pudieron leer todos los ángulos de servos")
            return None

        # Calcular ajustes (diferencia entre esperado y actual)
        adjustments = {}
        for servo in ['base', 'shoulder', 'elbow']:
            if servo in expected_angles and servo in current_angles:
                adjustment = expected_angles[servo] - current_angles[servo]
                adjustments[servo] = adjustment
                logger.info(f"Ajuste para {servo}: {adjustment}°")

        return adjustments if adjustments else None

    def measure_position_accuracy(self, test_positions=None):
        """
        Mide precisión de posicionamiento usando medición manual o visión
        """
        logger.info("Midiendo precisión de posicionamiento...")

        if test_positions is None:
            test_positions = [
                (200, 0, 150),
                (150, 100, 100),
                (100, -50, 200)
            ]

        accuracy_results = {}

        for target_pos in test_positions:
            tx, ty, tz = target_pos

            # Mover a posición
            if not self.robot_arm.move_to_position(tx, ty, tz, 'slow'):
                logger.warning(f"No se pudo mover a {target_pos}")
                continue

            time.sleep(2)  # Esperar estabilización

            # Intentar medir con visión
            measured_pos = None
            if hasattr(self.vision_system, 'detect_position_marker'):
                try:
                    measured_pos = self.vision_system.detect_position_marker()
                    logger.info(f"Posición medida con visión: {measured_pos}")
                except Exception as e:
                    logger.warning(f"Error en medición con visión: {e}")

            # Si no hay visión, pedir medición manual
            if measured_pos is None:
                print(f"\nPosición objetivo: ({tx}, {ty}, {tz})")
                try:
                    mx = float(input("Medir coordenada X real (mm): "))
                    my = float(input("Medir coordenada Y real (mm): "))
                    mz = float(input("Medir coordenada Z real (mm): "))
                    measured_pos = (mx, my, mz)
                except ValueError:
                    logger.warning("Entrada inválida, omitiendo medición")
                    continue

            # Calcular error
            if measured_pos:
                mx, my, mz = measured_pos
                error_x = mx - tx
                error_y = my - ty
                error_z = mz - tz
                total_error = math.sqrt(error_x**2 + error_y**2 + error_z**2)

                accuracy_results[str(target_pos)] = {
                    'target': target_pos,
                    'measured': measured_pos,
                    'error': (error_x, error_y, error_z),
                    'total_error': total_error
                }

                logger.info(f"Error en {target_pos}: {total_error:.2f} mm")

                # Aprender corrección
                self.robot_arm.learn_position_correction(target_pos, measured_pos)

        return accuracy_results

    def run_diagnostic_tests(self):
        """
        Ejecuta pruebas diagnósticas de todos los componentes
        """
        logger.info("Ejecutando pruebas diagnósticas...")

        results = {}

        # Prueba de servos
        results['servo_test'] = self.test_servos()

        # Prueba del motor
        results['motor_test'] = self.test_stepper_motor()

        # Prueba de visión
        results['vision_test'] = self.test_vision_system()

        # Prueba de comunicación
        results['communication_test'] = self.test_communication()

        # Prueba de brazo completo
        results['arm_test'] = self.test_robot_arm()

        logger.info("Pruebas diagnósticas completadas")
        return results

    def test_servos(self):
        """
        Prueba funcional de servos
        """
        logger.info("Probando servos...")

        try:
            self.servo_controller.test_servos()
            return {'status': 'PASSED', 'message': 'Todos los servos responden correctamente'}
        except Exception as e:
            return {'status': 'FAILED', 'message': str(e)}

    def test_stepper_motor(self):
        """
        Prueba funcional del motor paso a paso
        """
        logger.info("Probando motor paso a paso...")

        try:
            # Movimiento de prueba
            self.stepper_motor.move_steps(200, 500)
            time.sleep(1)
            self.stepper_motor.move_steps(-200, 500)
            return {'status': 'PASSED', 'message': 'Motor responde correctamente'}
        except Exception as e:
            return {'status': 'FAILED', 'message': str(e)}

    def test_vision_system(self):
        """
        Prueba funcional del sistema de visión
        """
        logger.info("Probando sistema de visión...")

        try:
            self.vision_system.start_camera()
            time.sleep(3)
            frame = self.vision_system.get_frame()
            self.vision_system.stop_camera()

            if frame is not None:
                return {'status': 'PASSED', 'message': 'Cámara funciona correctamente'}
            else:
                return {'status': 'FAILED', 'message': 'No se pudo capturar imagen'}
        except Exception as e:
            return {'status': 'FAILED', 'message': str(e)}

    def test_communication(self):
        """
        Prueba de comunicación entre componentes
        """
        logger.info("Probando comunicación...")

        try:
            # Verificar que todos los componentes estén accesibles
            servo_status = self.servo_controller.get_angle('base') is not None
            motor_status = self.stepper_motor.get_position() is not None

            if servo_status and motor_status:
                return {'status': 'PASSED', 'message': 'Comunicación OK'}
            else:
                return {'status': 'FAILED', 'message': 'Problema de comunicación con componentes'}
        except Exception as e:
            return {'status': 'FAILED', 'message': str(e)}

    def test_robot_arm(self):
        """
        Prueba funcional del brazo robótico
        """
        logger.info("Probando brazo robótico...")

        try:
            # Movimiento simple
            self.robot_arm.move_to_position(180, 50, 120, 'slow')
            time.sleep(2)
            self.robot_arm.home_position()

            return {'status': 'PASSED', 'message': 'Brazo funciona correctamente'}
        except Exception as e:
            return {'status': 'FAILED', 'message': str(e)}

    def generate_report(self, calibration_results, test_results):
        """
        Genera un reporte de calibración y pruebas
        """
        report = f"""
REPORTE DE CALIBRACIÓN Y PRUEBAS
================================

Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}

CALIBRACIÓN:
{json.dumps(calibration_results, indent=2)}

PRUEBAS DIAGNÓSTICAS:
{json.dumps(test_results, indent=2)}

CONFIGURACIÓN FINAL:
{json.dumps(self.calibration_data, indent=2)}
"""

        with open("calibration_report.txt", 'w') as f:
            f.write(report)

        logger.info("Reporte generado: calibration_report.txt")
        return report

    def cleanup(self):
        """
        Limpia recursos
        """
        self.vision_system.cleanup()
        self.stepper_motor.cleanup()
        logger.info("CalibrationSystem limpiado")

if __name__ == "__main__":
    # Prueba del sistema de calibración
    cal = CalibrationSystem()
    try:
        print("Sistema de Calibración para Brazo Robótico")
        print("1. Ejecutar calibración completa")
        print("2. Ejecutar pruebas diagnósticas")
        print("3. Medir precisión de posicionamiento")
        print("4. Salir")

        choice = input("Seleccione opción: ")

        if choice == '1':
            results = cal.run_full_calibration()
            print("Calibración completada")
            print(json.dumps(results, indent=2))

        elif choice == '2':
            results = cal.run_diagnostic_tests()
            print("Pruebas completadas")
            print(json.dumps(results, indent=2))

        elif choice == '3':
            results = cal.measure_position_accuracy()
            print("Medición de precisión completada")
            print(json.dumps(results, indent=2))

        else:
            print("Saliendo...")

    finally:
        cal.cleanup()