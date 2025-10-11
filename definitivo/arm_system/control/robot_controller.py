import time
import board
import busio
from adafruit_pca9685 import PCA9685
from gpiozero import OutputDevice
import logging as log

class ServoController:
    def __init__(self, i2c_address=0x40, frequency=50):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(self.i2c, address=i2c_address)
        self.pca.frequency = frequency
        self.servos = {}

    def add_servo(self, name, channel, min_pulse=500, max_pulse=2500, min_angle=0, max_angle=180):
        self.servos[name] = {
            'channel': channel,
            'min_pulse': min_pulse,
            'max_pulse': max_pulse,
            'min_angle': min_angle,
            'max_angle': max_angle
        }

    def set_angle(self, name, angle, speed=1.0):
        if name not in self.servos:
            log.error(f"Servo {name} not configured")
            return

        servo = self.servos[name]
        angle = max(servo['min_angle'], min(servo['max_angle'], angle))
        pulse = servo['min_pulse'] + (servo['max_pulse'] - servo['min_pulse']) * (angle / (servo['max_angle'] - servo['min_angle']))
        duty_cycle = int(pulse / 20000 * 0xFFFF)  # 50Hz period
        self.pca.channels[servo['channel']].duty_cycle = duty_cycle
        time.sleep(0.1 / speed)  # Simple speed control

class StepperController:
    def __init__(self, step_pin, dir_pin, enable_pin=None, steps_per_rev=200, microsteps=16):
        self.step_pin = OutputDevice(step_pin)
        self.dir_pin = OutputDevice(dir_pin)
        self.enable_pin = OutputDevice(enable_pin) if enable_pin else None
        self.steps_per_rev = steps_per_rev * microsteps
        self.current_position = 0

    def enable(self):
        if self.enable_pin:
            self.enable_pin.off()  # Assuming active low

    def disable(self):
        if self.enable_pin:
            self.enable_pin.on()

    def move_steps(self, steps, direction=1, speed=1000):  # steps per second
        self.dir_pin.value = 1 if direction > 0 else 0
        delay = 1.0 / speed
        for _ in range(abs(steps)):
            self.step_pin.on()
            time.sleep(delay / 2)
            self.step_pin.off()
            time.sleep(delay / 2)
        self.current_position += steps * direction

    def move_distance(self, distance_mm, lead_screw_pitch=8, direction=1, speed=1000):
        steps = int((distance_mm / lead_screw_pitch) * self.steps_per_rev)
        self.move_steps(steps, direction, speed)

class RobotController:
    def __init__(self):
        self.servo_controller = ServoController()
        # Configure servos: base (channel 0), shoulder (1), elbow (2), gripper (3)
        self.servo_controller.add_servo('base', 0)
        self.servo_controller.add_servo('shoulder', 1)
        self.servo_controller.add_servo('elbow', 2)
        self.servo_controller.add_servo('gripper', 3)

        # Stepper for arm lift: step=17, dir=18, enable=19 (BCM pins)
        self.stepper_controller = StepperController(step_pin=17, dir_pin=18, enable_pin=19)

    def move_base(self, angle, speed=30):
        self.servo_controller.set_angle('base', angle, speed)

    def move_shoulder(self, angle, speed=30):
        self.servo_controller.set_angle('shoulder', angle, speed)

    def move_elbow(self, angle, speed=30):
        self.servo_controller.set_angle('elbow', angle, speed)

    def move_gripper(self, angle, speed=30):
        self.servo_controller.set_angle('gripper', angle, speed)

    def move_arm(self, distance_mm, direction=1, speed=1000):
        self.stepper_controller.move_distance(distance_mm, direction=direction, speed=speed)

    def pick_action(self):
        self.move_gripper(0)  # Open

    def place_action(self):
        self.move_gripper(90)  # Close

    def up_action(self, distance=50):
        self.move_arm(distance, direction=1)

    def close(self):
        self.stepper_controller.disable()
        self.servo_controller.pca.deinit()