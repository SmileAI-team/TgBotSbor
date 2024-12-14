import os
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from PIL import Image, ImageDraw
from typing import List, Tuple
from transform import image_to_numpy
from neiro import MouthImage, CariesTooth

class Caries:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise ValueError(f"Can't find model with path {model_path}")
        self.model = YOLO(model_path)
        self.names = {
            0: "Обнаружен Кариес",
            1: "Небольшое повреждение",
            2: "Здоров ",
        }
        print(f"Model loaded with classes: {self.names}")

    def analyze(self, mouth_image: MouthImage):
        """
        Анализирует изображение рта и обновляет caries_coord в mouth_image.

        Args:
            mouth_image (MouthImage): Датакласс, содержащий изображение рта и информацию о зубах.

        Returns:
            MouthImage: Обновленный mouth_image с заполненным caries_coord и caries_type.
        """
        for tooth in mouth_image.boxes:
            # Анализируем массив изображения зуба
            predicted_class = self.analyze_array(tooth.tooth_array)

            # Если класс относится к 0 (Обнаружен Кариес) или 1 (Небольшое повреждение)
            if predicted_class in [0, 1]:
                # Добавляем координаты зуба в caries_coord
                caries_tooth = CariesTooth(
                    caries_coord=tooth.tooth_coord,  # Координаты зуба
                    caries_type=predicted_class  # Тип кариеса
                )
                mouth_image.caries_coord.append(caries_tooth)


    def analyze_array(self, image_array: np.ndarray) -> int:
        """
        Анализирует входной массив изображения и возвращает однозначный класс (0, 1, 2).

        Args:
            image_array (np.ndarray): Массив изображения.

        Returns:
            int: Класс (0, 1, 2), соответствующий предсказанию модели.
        """
        results = self.model(image_array, save=False)

        # Проверяем, есть ли боксы в результатах
        if len(results[0].boxes) == 0:
            raise ValueError("Model did not detect any objects in the image.")

        # Извлекаем первый бокс (или используем максимальное значение уверенности)
        box = max(results[0].boxes, key=lambda b: b.conf.cpu().item())

        # Получаем класс из предсказания
        predicted_class = int(box.cls.cpu().item())
        return predicted_class


model_path = Path("../models/kaif_caries.pt")
caries_model = Caries(model_path)

# img = image_to_numpy("./results/cropped_boxes/box_10.jpg")
#
# print(caries_model.analyze_array(img))