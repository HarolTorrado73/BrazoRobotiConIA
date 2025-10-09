#!/usr/bin/env python3
"""
Sistema de visión para brazo robótico
Incluye detección de objetos, seguimiento y calibración visual
"""

import cv2
import numpy as np
import time
import logging
import math
from picamera2 import Picamera2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionSystem:
    def __init__(self):
        """
        Inicializa el sistema de visión con SHCHV 5MP
        """
        self.camera = None
        self.is_running = False
        self.target_object = None
        self.detected_objects = []
        self.calibration_data = {}

        # Configuración para SHCHV 5MP
        self.camera_config = {
            'size': (2592, 1944),  # Resolución máxima 5MP
            'format': 'RGB888',
            'fps': 30
        }

        logger.info("VisionSystem inicializado con SHCHV 5MP")

    def start_camera(self):
        """
        Inicia la cámara SHCHV 5MP usando picamera2
        """
        try:
            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"size": self.camera_config['size'], "format": self.camera_config['format']}
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2)  # Esperar inicialización

            self.is_running = True
            logger.info(f"Cámara SHCHV 5MP iniciada con resolución {self.camera_config['size']}")
            return True
        except Exception as e:
            logger.error(f"Error iniciando cámara SHCHV 5MP: {e}")
            return False

    def stop_camera(self):
        """
        Detiene la cámara
        """
        if self.camera:
            self.camera.release()
            self.camera = None
        self.is_running = False
        logger.info("Cámara detenida")

    def get_frame(self):
        """
        Captura un frame de la cámara SHCHV 5MP
        """
        if not self.is_running or not self.camera:
            return None

        try:
            frame = self.camera.capture_array()
            # Convertir de RGB a BGR para compatibilidad con OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            logger.error(f"Error capturando frame: {e}")
            return None

    def detect_objects(self, frame):
        """
        Detecta objetos en el frame (implementación básica con color)
        """
        if frame is None:
            return []

        # Convertir a HSV para mejor detección de color
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Definir rangos de color para objetos (ejemplo: rojo)
        lower_red = np.array([0, 120, 70])
        upper_red = np.array([10, 255, 255])

        # Máscara
        mask = cv2.inRange(hsv, lower_red, upper_red)

        # Encontrar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        objects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Filtrar objetos pequeños
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                objects.append({
                    'label': 'red_object',
                    'bbox': (x, y, w, h),
                    'center': (center_x, center_y),
                    'area': area
                })

        self.detected_objects = objects
        return objects

    def detect_position_marker(self):
        """
        Detecta un marcador de posición para calibración
        Retorna coordenadas (x, y, z) en mm relativas al robot
        """
        frame = self.get_frame()
        if frame is None:
            return None

        # Buscar círculos (marcadores redondos)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)

        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                   param1=50, param2=30, minRadius=10, maxRadius=50)

        if circles is not None:
            circles = np.uint16(np.around(circles))
            # Tomar el círculo más grande
            largest_circle = max(circles[0], key=lambda c: c[2])

            x, y, radius = largest_circle

            # Convertir coordenadas de píxel a mundo real (calibración necesaria)
            # Valores de ejemplo - ajustar según calibración
            scale_x = 0.5  # mm por píxel
            scale_y = 0.5
            offset_x = 320  # centro de imagen
            offset_y = 240

            world_x = (x - offset_x) * scale_x
            world_y = 200  # Distancia fija hacia adelante (ajustar)
            world_z = (offset_y - y) * scale_y + 100  # Altura

            logger.info(f"Marcador detectado en píxel ({x}, {y}), mundo ({world_x:.1f}, {world_y:.1f}, {world_z:.1f})")
            return (world_x, world_y, world_z)

        return None

    def set_target_object(self, label):
        """
        Establece el objeto a seguir
        """
        self.target_object = label
        logger.info(f"Objeto objetivo establecido: {label}")

    def get_target_position(self):
        """
        Obtiene la posición del objeto objetivo
        """
        frame = self.get_frame()
        if frame is None:
            return None

        objects = self.detect_objects(frame)

        for obj in objects:
            if obj['label'] == self.target_object:
                x, y, w, h = obj['bbox']
                # Convertir a coordenadas del robot (calibración necesaria)
                world_x = (x + w//2 - 320) * 0.5  # Ejemplo simple
                world_y = 200
                world_z = 150
                return (world_x, world_y, world_z, w, h)

        return None

    def calibrate_camera(self, known_positions):
        """
        Calibración de la cámara usando posiciones conocidas
        """
        logger.info("Iniciando calibración de cámara...")

        # Capturar imágenes de marcadores en posiciones conocidas
        calibration_points = []

        for world_pos in known_positions:
            print(f"Coloque marcador en posición: {world_pos}")
            input("Presione Enter cuando esté listo...")

            marker_pos = self.detect_position_marker()
            if marker_pos:
                calibration_points.append((world_pos, marker_pos))
                logger.info(f"Punto calibrado: mundo {world_pos} -> imagen {marker_pos}")
            else:
                logger.warning("No se detectó marcador")

        # Calcular transformación (simplificada)
        if len(calibration_points) >= 3:
            # Aquí iría cálculo de matriz de transformación
            # Por ahora, guardar puntos para referencia
            self.calibration_data['calibration_points'] = calibration_points
            logger.info("Calibración de cámara completada")
        else:
            logger.warning("Insuficientes puntos de calibración")

    def cleanup(self):
        """
        Limpia recursos
        """
        self.stop_camera()
        logger.info("VisionSystem limpiado")

if __name__ == "__main__":
    # Prueba del sistema de visión
    vision = VisionSystem()
    try:
        if vision.start_camera():
            while True:
                frame = vision.get_frame()
                if frame is not None:
                    objects = vision.detect_objects(frame)
                    print(f"Objetos detectados: {len(objects)}")

                    # Mostrar frame
                    cv2.imshow('Vision System', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                time.sleep(0.1)
    finally:
        vision.cleanup()
        cv2.destroyAllWindows()