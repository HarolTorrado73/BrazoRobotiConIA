import time
import logging as log
from control.robot_controller import RobotController

log.basicConfig(level=log.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Robot:
    def __init__(self):
        self.robot_controller = RobotController()

        # register scan data
        self.scan_results = []

        # zones
        self.placement_zones = {
            'apple': {'angle': 90, 'distance': 200},
            'orange': {'angle': 180, 'distance': 200},
            'bottle': {'angle': 45, 'distance': 200},
            'default': {'angle': 270, 'distance': 200},
        }
        
    # --- MENU ---
    def main_menu_loop(self):
        running = True
        while running:
            print("\n=== Main menu ===")
            print(" [c] check service")
            print(" [s] safety service")
            print(" [n] scan service")
            print(" [p] pick & place service")
            print(" [q] exit")
            
            user_input = input("input command: ").strip().lower()

            if user_input == 'c':
                self.serial_manager.send_message('check_service', {})
                
            elif user_input == 's':
                self.serial_manager.send_message('safety_service', {})
                
            elif user_input == 'n':
                self.handle_scan_command()
                
            elif user_input == 'p':
                self.handle_pick_place_command()
                
            elif user_input == 'q':
                running = False
                
            else:
                print("command unrecognized")
            
            time.sleep(0.5)
            
    # --- SCAN ---
    def handle_scan_command(self):
        """scan command"""

        from perception.vision.camera.main import CameraManager
        from perception.vision.detection.main import DetectionModel

        self.scan_results = []

        camera = CameraManager()
        detector = DetectionModel()

        log.info("scanning in progress...")

        # Capture image
        image_path = camera.capture_image()
        if not image_path:
            log.error("failed to capture image")
            return

        # Load image
        import cv2
        image = cv2.imread(image_path)

        # Detect objects
        results, names = detector.inference(image)

        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                # Simulate angle and distance based on position
                angle = (center_x / image.shape[1]) * 180  # rough estimate
                distance = 200  # fixed for now

                data = {
                    'class': names[cls],
                    'confidence': conf,
                    'angle': angle,
                    'distance': distance,
                    'image_path': image_path
                }
                self._scan_callback(data)

        self.process_scan_results()
        
    def _scan_callback(self, data):
        if data.get('class'):
            self._update_object_registry(data)
            
    def _update_object_registry(self, data: dict):
        """update object registry"""
        try:
            self.scan_results.append({
                'position': {
                    'angle': data.get('angle', 0),
                    'distance': data.get('distance', 0)
                },
                'detection':{
                    'class': data.get('class', 'default'),
                    'confidence': data.get('confidence', 0.0),
                    'image': data.get('image_path', '')
                },
                'placement_zone': self._get_placement_zones(data.get('class', 'default'))
            })
        except Exception as e:
            log.error(f"error updating registry: {str(e)}")
        
    def _get_placement_zones(self, object_class: str):
        return self.placement_zones.get(object_class.lower(), 
                                        self.placement_zones['default'])          
        
    def process_scan_results(self):
        """process scan data"""
        if not self.scan_results:
            log.warning("scanning completed without object detection")
            return
            
        log.info(f"\n=== objects scanned: ({len(self.scan_results)}) ===")
        processed_list = []
        for i, obj in enumerate(self.scan_results, start=1):
            angle = obj['position']['angle']
            distance = obj['position']['distance']
            obj_class = obj['detection']['class']
            confidence = obj['detection']['confidence']
            zone = obj['placement_zone']

            item = {
                'index': i,
                'center_angle': angle,
                'distance': distance,
                'class': obj_class,
                'confidence': confidence,
                'placement_zone': zone
            }
            processed_list.append(item)

            log.info(f"Obj {i} -> angle: {angle}°, distance: {distance}mm, class: {obj_class}, conf: {confidence:.2f}")

        self.scan_results = processed_list
    
    # --- PICK & PLACE ---
    def handle_pick_place_command(self):
        """pick & place command"""
        if not self.scan_results:
            log.warning("1. first scanning the enviroment (option 'n')")
            return

        selected_object = self.select_object_interactively()
        if not selected_object:
            return

        log.info(f"\ninit pick & place to object: {selected_object['index']}:")
        log.info(f"angle: {selected_object['center_angle']}°")
        log.info(f"distance: {selected_object['distance']} mm")
        
        if self.execute_pick_sequence(selected_object):
            log.info(f"¡pick completed!")
            if self.execute_place_sequence(selected_object):
                log.info(f"¡pick and place completed!")
                
    def select_object_interactively(self):
        """interface for object selection"""
        print("\n=== OBJECTS DETECTED LIST ===")
        for o in self.scan_results:
            i = o['index']
            print(f"[{i}] angle={o['center_angle']}° dist={o['distance']}mm class={o['class']} conf={o['confidence']:.2f}")
        print("[0] cancelar")
        
        try:
            selection = int(input("\nselect the object you want to take: "))
            if selection == 0:
                print("operation canceled")
                return {}
            
            return next((x for x in self.scan_results if x['index'] == selection), {})
        
        except ValueError:
            print("invalid input")
            return {}
        
    def execute_pick_sequence(self, target_object: dict) -> bool:
        try:
            plan = [
                {'joint': 'base', 'angle': target_object['center_angle'], 'speed': 30},
                {'joint': 'arm', 'distance': target_object['distance'], 'action': 'pick'},
                {'joint': 'gripper', 'action': 'close'},
                {'joint': 'arm', 'distance': target_object['distance'], 'action': 'up'},
            ]
            self.execute_movement('pick_service', plan)
            return True
        except Exception as e:
            log.error(f"Error in pick sequence: {e}")
            return False
        
    def execute_place_sequence(self, target_object: dict):
        """execute object in place"""
        try:
            zone_params = target_object['placement_zone']
            movement_plan = [
                {'joint': 'base', 'angle': zone_params['angle'], 'speed': 30},
                {'joint': 'arm', 'distance': zone_params['distance'], 'action': 'place'},
                {'joint': 'gripper', 'action': 'open'},
                {'joint': 'arm', 'distance': target_object['distance'], 'action': 'up'},
                {'joint': 'base', 'angle': 0, 'speed': 60},  # Regresar a base 0
            ]
            self.execute_movement('place_service', movement_plan)
            return True
        except Exception as e:
            log.error(f"Error in place sequence: {e}")
            return False
        
            
    def get_current_angles(self) -> dict:
        """get current angles (estimated)"""
        # Since no encoders, return default or last known
        return {'base': 0, 'shoulder': 90, 'elbow': 90, 'gripper': 0}
        
    def execute_movement(self, message_type: str, movement_sequence: list):
        """execute movements on arm"""
        log.info("\nexecution movements:")

        for move in movement_sequence:
            try:
                joint = move['joint']
                log.info(f"movement: {joint}")

                # execute movement
                if joint == 'base':
                    self.robot_controller.move_base(move['angle'], move.get('speed', 30))
                elif joint == 'arm':
                    if 'action' in move:
                        if move['action'] == 'pick':
                            self.robot_controller.move_arm(move['distance'], direction=-1)  # down
                        elif move['action'] == 'up':
                            self.robot_controller.up_action(move.get('distance', 50))
                        elif move['action'] == 'place':
                            self.robot_controller.move_arm(move['distance'], direction=-1)  # down
                    else:
                        self.robot_controller.move_arm(move['distance'], direction=1)
                elif joint == 'gripper':
                    if move['action'] == 'close':
                        self.robot_controller.place_action()
                    elif move['action'] == 'open':
                        self.robot_controller.pick_action()

                # log
                log.info(f"-> ¡Movement {joint} completed!")

            except Exception as e:
                log.error(f'error in movement: {str(e)}')
                self.handle_movement_failure()
                raise
            
    def handle_movement_failure(self):
        """Handles faults in the motion sequence"""
        log.error('executing security protocol')
        # Move to safe position
        try:
            self.robot_controller.move_base(0)
            self.robot_controller.move_shoulder(90)
            self.robot_controller.move_elbow(90)
            self.robot_controller.move_gripper(0)
            self.robot_controller.up_action(100)  # Move up
            log.info("system safety - moved to safe position")
        except Exception as e:
            log.error(f"error in safety: {e}")
            self.robot_controller.close()
            exit(1)
            
            
    def run(self):
        try:
            log.info("starting robot controller")
            self.main_menu_loop()

        except KeyboardInterrupt:
            log.info("Programa interrumpido por el usuario.")
        finally:
            log.info("closing robot controller.")
            self.robot_controller.close()


if __name__ == '__main__':
    robot = Robot()
    robot.run()
