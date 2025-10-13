#!/usr/bin/env python3
"""
Move Robot Arm with Calibrated Angles
Uses the angles registered in manual_control.py to move the physical arm
"""

import time
import logging as log
try:
    from .control.robot_controller import ControladorRobotico
except ImportError:
    # Fallback for Windows testing
    from control.robot_controller import ControladorRobotico

log.basicConfig(level=log.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class CalibratedMover:
    def __init__(self):
        self.controlador_robot = ControladorRobotico()
        # Ángulos calibrados - CAMBIA estos valores por los que calibraste
        self.calibrated_angles = {
            'base': 30,      # ← TU VALOR CALIBRADO AQUÍ
            'shoulder': 45,  # ← TU VALOR CALIBRADO AQUÍ
            'elbow': 90,     # ← TU VALOR CALIBRADO AQUÍ
            'gripper': 0     # ← TU VALOR CALIBRADO AQUÍ
        }
        log.info("Calibrated Mover initialized")

    def run(self):
        """Main calibrated movement interface"""
        print("\n" + "="*50)
        print("🤖 MOVIMIENTO CON ÁNGULOS CALIBRADOS")
        print("="*50)
        print("INSTRUCCIONES:")
        print("1. Asegúrate de que la alimentación esté CONECTADA")
        print("2. El brazo se moverá a las posiciones calibradas")
        print("\nComandos:")
        print("  b<ángulo> - Mover base (0-360°)")
        print("  s<ángulo> - Mover hombro (0-360°)")
        print("  e<ángulo> - Mover codo (0-360°)")
        print("  g<ángulo> - Mover pinza (0-360°)")
        print("  home      - Ir a posición calibrada")
        print("  test      - Probar movimientos suaves")
        print("  q         - Salir")
        print("\nEjemplo de uso:")
        print("  b90       - Base a 90°")
        print("  s45       - Hombro a 45°")
        print("  e120      - Codo a 120°")
        print("  home      - Posición calibrada")
        print("="*50)

        while True:
            try:
                cmd = input("\nmover> ").strip().lower()

                if cmd == 'q':
                    break
                elif cmd == 'home':
                    self.go_to_calibrated_position()
                elif cmd == 'test':
                    self.test_movements()
                elif cmd.startswith(('b', 's', 'e', 'g')):
                    self.move_to_angle(cmd)
                else:
                    print("❌ Usa: b<ángulo>, s<ángulo>, e<ángulo>, g<ángulo>, home, test, q")

            except KeyboardInterrupt:
                print("\n👋 Saliendo del movimiento calibrado...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        self.cleanup()

    def move_to_angle(self, cmd):
        """Move specific joint to angle"""
        try:
            joint_map = {
                'b': ('base', 'Base'),
                's': ('shoulder', 'Hombro'),
                'e': ('elbow', 'Codo'),
                'g': ('gripper', 'Pinza')
            }

            joint, display_name = joint_map[cmd[0]]
            angle = int(cmd[1:])

            # Validar límites - todos los servos configurados para 360°
            if not (0 <= angle <= 360):
                print(f"❌ El ángulo debe estar entre 0-360°")
                return

            print(f"🔄 Moviendo {display_name} a {angle}°...")

            if joint == 'base':
                self.controlador_robot.mover_base(angle, velocidad=2)
            elif joint == 'shoulder':
                self.controlador_robot.mover_hombro(angle, velocidad=2)
            elif joint == 'elbow':
                self.controlador_robot.mover_codo(angle, velocidad=2)
            elif joint == 'gripper':
                self.controlador_robot.mover_pinza(angle, velocidad=2)

            print(f"✅ {display_name} movido a {angle}°")

        except ValueError:
            print("❌ Formato inválido. Usa: b90, s45, etc.")
        except Exception as e:
            print(f"❌ Error de movimiento: {e}")

    def go_to_calibrated_position(self):
        """Move to calibrated home position"""
        print("🏠 Yendo a posición calibrada...")
        try:
            self.controlador_robot.mover_base(self.calibrated_angles['base'], velocidad=2)
            time.sleep(0.3)
            self.controlador_robot.mover_hombro(self.calibrated_angles['shoulder'], velocidad=2)
            time.sleep(0.3)
            self.controlador_robot.mover_codo(self.calibrated_angles['elbow'], velocidad=2)
            time.sleep(0.3)
            self.controlador_robot.mover_pinza(self.calibrated_angles['gripper'], velocidad=2)
            print("✅ Posición calibrada alcanzada")
        except Exception as e:
            print(f"❌ Error yendo a posición calibrada: {e}")

    def test_movements(self):
        """Test calibrated movements with small adjustments"""
        print("🧪 Probando movimientos calibrados...")

        try:
            # Test base
            print("Base...")
            current = self.calibrated_angles['base']
            self.controlador_robot.mover_base(current + 10, velocidad=1)
            time.sleep(0.3)
            self.controlador_robot.mover_base(current, velocidad=1)
            time.sleep(0.3)

            # Test shoulder
            print("Hombro...")
            current = self.calibrated_angles['shoulder']
            self.controlador_robot.mover_hombro(current + 5, velocidad=1)
            time.sleep(0.3)
            self.controlador_robot.mover_hombro(current, velocidad=1)
            time.sleep(0.3)

            # Test gripper
            print("Pinza...")
            self.controlador_robot.mover_pinza(90, velocidad=1)
            time.sleep(0.3)
            self.controlador_robot.mover_pinza(0, velocidad=1)

            print("✅ Prueba completada")

        except Exception as e:
            print(f"❌ Error en prueba: {e}")

    def cleanup(self):
        """Clean shutdown"""
        print("🔌 Apagando...")
        try:
            self.controlador_robot.cerrar()
            print("✅ Movimiento calibrado cerrado")
        except Exception as e:
            print(f"❌ Error durante apagado: {e}")


if __name__ == '__main__':
    mover = CalibratedMover()
    mover.run()