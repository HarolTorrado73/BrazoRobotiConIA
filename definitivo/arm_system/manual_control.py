#!/usr/bin/env python3
"""
Manual Control Interface for Robot Arm
Control individual joints with simple commands
"""

import time
import logging as log
try:
    from .control.robot_controller import ControladorRobotico
except ImportError:
    # Fallback for Windows testing
    from control.robot_controller import ControladorRobotico

log.basicConfig(level=log.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ManualController:
    def __init__(self):
        self.controlador_robot = ControladorRobotico()
        # Estado actual de cada articulación
        self.current_angles = {
            'base': 180,      # Posición home
            'shoulder': 45,   # Posición home
            'elbow': 0,      # Posición home
            'gripper': 0      # Abierta
        }
        # No necesitamos selección de articulaciones para calibración manual
        log.info("Manual Controller initialized")

    def run(self):
        """Main manual control loop"""
        print("\n" + "="*50)
        print("🤖 CONTROL MANUAL DEL BRAZO ROBÓTICO")
        print("="*50)
        print("CALIBRACIÓN MANUAL - MUEVE TÚ EL BRAZO")
        print("\nINSTRUCCIONES:")
        print("1. DESCONECTA la alimentación de los servos")
        print("2. Mueve MANUALMENTE cada articulación del brazo")
        print("3. Usa los comandos para REGISTRAR los ángulos")
        print("\nComandos:")
        print("  b<ángulo> - Registrar ángulo base (ej: b90)")
        print("  s<ángulo> - Registrar ángulo hombro (ej: s45)")
        print("  e<ángulo> - Registrar ángulo codo (ej: e90)")
        print("  g<ángulo> - Registrar ángulo pinza (ej: g0)")
        print("  r         - Mostrar ángulos registrados")
        print("  c         - Limpiar todos los ángulos")
        print("  q         - Salir")
        print("\nEjemplo de uso:")
        print("  Mueve base manualmente a 90° → escribe 'b90'")
        print("  Mueve hombro a 45° → escribe 's45'")
        print("  Presiona 'r' para ver todos los ángulos")
        print("="*50)
        self.show_current_angles()

        while True:
            try:
                cmd = input("\ncalibrar> ").strip().lower()

                if cmd == 'q':
                    break
                elif cmd == 'r':
                    self.show_current_angles()
                elif cmd == 'c':
                    self.clear_angles()
                elif cmd.startswith(('b', 's', 'e', 'g')):
                    self.parse_command(cmd)
                else:
                    print("❌ Usa: b<ángulo>, s<ángulo>, e<ángulo>, g<ángulo>, r (mostrar), c (limpiar), q (salir)")

            except KeyboardInterrupt:
                print("\n👋 Saliendo del control manual...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        self.show_current_angles()
        self.cleanup()

    def parse_command(self, cmd):
        """Parse and execute manual command"""
        try:
            if cmd[0] in ['b', 's', 'e', 'g']:
                # Servo control
                joint_map = {
                    'b': ('base', 'Base'),
                    's': ('shoulder', 'Hombro'),
                    'e': ('elbow', 'Codo'),
                    'g': ('gripper', 'Pinza')
                }

                joint, display_name = joint_map[cmd[0]]
                angle = int(cmd[1:])

                # Todos los servos configurados para 360°
                if not (0 <= angle <= 360):
                    print(f"❌ El ángulo debe estar entre 0-360°")
                    return

                # SOLO registrar el ángulo - NO mover físicamente
                self.current_angles[joint] = angle
                print(f"✅ REGISTRADO: {display_name} en {angle}°")

            elif cmd.startswith('a'):
                # Arm control
                try:
                    distance = int(cmd[1:])
                except ValueError:
                    print("❌ Formato de distancia inválido")
                    return

                direction = "ARRIBA" if distance > 0 else "ABAJO"
                distance = abs(distance)

                # SOLO registrar movimiento - NO mover físicamente
                print(f"✅ REGISTRADO: Brazo {direction} {distance}mm")

        except ValueError:
            print("❌ Formato de número inválido. Usa: b90, s45, a50, etc.")
        except Exception as e:
            print(f"❌ Error de movimiento: {e}")

    def adjust_angle(self, delta):
        """Adjust current joint by delta degrees"""
        if self.selected_joint == 'arm':
            # Para el brazo, ajustar arriba/abajo
            direction = 1 if delta > 0 else -1
            distance = abs(delta)
            # SOLO registrar movimiento - NO mover físicamente
            print(f"✅ REGISTRADO: Brazo {'ARRIBA' if direction > 0 else 'ABAJO'} {distance}mm")
        else:
            # Para servos - movimientos más pequeños y lentos
            current = self.current_angles[self.selected_joint]
            new_angle = current + delta

            # Validar límites - todos los servos configurados para 360°
            new_angle = max(0, min(360, new_angle))

            if new_angle != current:
                joint_names = {
                    'base': 'Base',
                    'shoulder': 'Hombro',
                    'elbow': 'Codo',
                    'gripper': 'Pinza'
                }

                display_name = joint_names[self.selected_joint]
                # SOLO registrar el ángulo - NO mover físicamente
                self.current_angles[self.selected_joint] = new_angle
                print(f"✅ REGISTRADO: {display_name} en {new_angle}°")
            else:
                print("📍 Límite alcanzado")

    def select_next_joint(self):
        """Select next joint"""
        current_index = self.joint_names.index(self.selected_joint)
        next_index = (current_index + 1) % len(self.joint_names)
        self.selected_joint = self.joint_names[next_index]
        print(f"🔄 Articulación seleccionada: {self.selected_joint}")

    def select_previous_joint(self):
        """Select previous joint"""
        current_index = self.joint_names.index(self.selected_joint)
        prev_index = (current_index - 1) % len(self.joint_names)
        self.selected_joint = self.joint_names[prev_index]
        print(f"🔄 Articulación seleccionada: {self.selected_joint}")

    def show_current_angles(self):
        """Show current angles of all joints"""
        print("\n📊 ÁNGULOS REGISTRADOS:")
        print(f"  Base:     {self.current_angles['base']}°")
        print(f"  Hombro:   {self.current_angles['shoulder']}°")
        print(f"  Codo:     {self.current_angles['elbow']}°")
        print(f"  Pinza:    {self.current_angles['gripper']}°")

    def clear_angles(self):
        """Clear all registered angles"""
        self.current_angles = {
            'base': 0,
            'shoulder': 0,
            'elbow': 0,
            'gripper': 0
        }
        print("✅ Todos los ángulos limpiados")

    def go_home(self):
        """Move all joints to home position"""
        print("🏠 SIMULANDO posición home...")
        try:
            # Solo actualizar estado - no mover físicamente
            self.current_angles = {
                'base': 180,
                'shoulder': 45,
                'elbow': 90,
                'gripper': 0
            }
            print("✅ SIMULADO: Posición home alcanzada")
            self.show_current_angles()
        except Exception as e:
            print(f"❌ Error en simulación: {e}")

    def test_sequence(self):
        """Run a test sequence to verify all movements"""
        print("🧪 Ejecutando secuencia de prueba...")

        try:
            # Test base rotation (con servo 360°)
            print("Probando base...")
            self.controlador_robot.mover_base(90, velocidad=2)
            time.sleep(0.5)
            self.controlador_robot.mover_base(270, velocidad=2)
            time.sleep(0.5)
            self.controlador_robot.mover_base(180, velocidad=2)  # Posición home
            time.sleep(0.5)

            # Test shoulder
            print("Probando hombro...")
            self.controlador_robot.mover_hombro(30, velocidad=2)  # Menos inclinado
            time.sleep(0.5)
            self.controlador_robot.mover_hombro(60, velocidad=2)
            time.sleep(0.5)
            self.controlador_robot.mover_hombro(45, velocidad=2)  # Posición home
            time.sleep(0.5)

            # Test elbow
            print("Probando codo...")
            self.controlador_robot.mover_codo(45, velocidad=2)
            time.sleep(0.5)
            self.controlador_robot.mover_codo(135, velocidad=2)
            time.sleep(0.5)
            self.controlador_robot.mover_codo(90, velocidad=2)
            time.sleep(0.5)

            # Test gripper
            print("Probando pinza...")
            self.controlador_robot.mover_pinza(90, velocidad=2)  # Cerrar
            time.sleep(0.5)
            self.controlador_robot.mover_pinza(0, velocidad=2)   # Abrir
            time.sleep(0.5)

            # Test arm
            print("Probando brazo...")
            self.controlador_robot.mover_brazo(20, direccion=-1, velocidad=100)  # Abajo
            time.sleep(0.5)
            self.controlador_robot.mover_brazo(20, direccion=1, velocidad=100)   # Arriba
            time.sleep(0.5)

            print("✅ Secuencia de prueba completada!")

        except Exception as e:
            print(f"❌ Prueba fallida: {e}")

    def cleanup(self):
        """Clean shutdown"""
        print("🔌 Apagando...")
        try:
            self.controlador_robot.cerrar()
            print("✅ Control manual cerrado")
        except Exception as e:
            print(f"❌ Error durante apagado: {e}")


if __name__ == '__main__':
    controller = ManualController()
    controller.run()
