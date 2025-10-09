#!/usr/bin/env python3
"""
Script de prueba de integración completa
Verifica que todos los componentes funcionen correctamente
"""

import time
import logging
import sys
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Prueba que todas las dependencias se importen correctamente"""
    print("🧪 Probando imports...")

    tests = [
        ("RPi.GPIO", "import RPi.GPIO as GPIO"),
        ("Adafruit ServoKit", "from adafruit_servokit import ServoKit"),
        ("TMC2209", "from tmc2209 import TMC2209"),
        ("Picamera2", "from picamera2 import Picamera2"),
        ("OpenCV", "import cv2"),
        ("NumPy", "import numpy as np"),
        ("RobotArm", "from robot_arm import RobotArm"),
        ("ServoController", "from servo_controller import ServoController"),
        ("StepperMotor", "from stepper_motor import StepperMotor"),
        ("VisionSystem", "from vision_system import VisionSystem"),
        ("CalibrationSystem", "from calibration_system import CalibrationSystem")
    ]

    passed = 0
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
            passed += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
        except Exception as e:
            print(f"⚠️  {name}: Error inesperado - {e}")

    print(f"\n📊 Imports: {passed}/{len(tests)} exitosos")
    return passed == len(tests)

def test_hardware_initialization():
    """Prueba inicialización de hardware (sin movimiento)"""
    print("\n🔧 Probando inicialización de hardware...")

    try:
        from servo_controller import ServoController
        servo = ServoController()
        print("✅ ServoController inicializado")
        servo.cleanup()
    except Exception as e:
        print(f"❌ ServoController: {e}")
        return False

    try:
        from stepper_motor import StepperMotor
        stepper = StepperMotor()
        print("✅ StepperMotor inicializado")
        stepper.cleanup()
    except Exception as e:
        print(f"❌ StepperMotor: {e}")
        return False

    try:
        from vision_system import VisionSystem
        vision = VisionSystem()
        print("✅ VisionSystem inicializado")
        vision.cleanup()
    except Exception as e:
        print(f"❌ VisionSystem: {e}")
        return False

    return True

def test_robot_arm():
    """Prueba inicialización del brazo robótico"""
    print("\n🤖 Probando RobotArm...")

    try:
        from robot_arm import RobotArm
        arm = RobotArm()
        print("✅ RobotArm inicializado")

        # Verificar que cargó calibración
        if hasattr(arm, 'calibration_data'):
            print("✅ Datos de calibración cargados")
        else:
            print("⚠️  Sin datos de calibración")

        # Verificar dimensiones
        print(f"📏 Dimensiones del brazo: {arm.link_lengths}")

        arm.servo_controller.cleanup()
        arm.stepper_motor.cleanup()
        return True

    except Exception as e:
        print(f"❌ RobotArm: {e}")
        return False

def test_calibration_system():
    """Prueba sistema de calibración"""
    print("\n🎯 Probando CalibrationSystem...")

    try:
        from calibration_system import CalibrationSystem
        cal = CalibrationSystem()
        print("✅ CalibrationSystem inicializado")

        # Verificar datos de calibración
        if hasattr(cal, 'calibration_data'):
            print("✅ Datos de calibración disponibles")
            print(f"📊 Offsets de servos: {cal.calibration_data.get('servo_offsets', {})}")

        cal.cleanup()
        return True

    except Exception as e:
        print(f"❌ CalibrationSystem: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 PRUEBA DE INTEGRACIÓN COMPLETA")
    print("=" * 40)

    # Verificar entorno virtual
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Advertencia: No se detecta entorno virtual activo")
        print("   Recomendado: source robot_env/bin/activate")

    results = []

    # Ejecutar pruebas
    results.append(("Imports", test_imports()))
    results.append(("Hardware Init", test_hardware_initialization()))
    results.append(("RobotArm", test_robot_arm()))
    results.append(("Calibration", test_calibration_system()))

    # Resumen
    print("\n" + "=" * 40)
    print("📋 RESUMEN DE PRUEBAS")

    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Resultado: {passed}/{len(results)} pruebas pasaron")

    if passed == len(results):
        print("\n🎉 ¡TODA LA INTEGRACIÓN FUNCIONA CORRECTAMENTE!")
        print("   Puedes proceder con la calibración y uso del brazo robótico.")
        return True
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
        print("   Asegúrate de que el hardware esté conectado correctamente.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)