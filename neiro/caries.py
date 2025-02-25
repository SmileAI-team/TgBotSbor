import os
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from PIL import Image, ImageDraw
from typing import List, Tuple
from .transform import image_to_numpy
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

    def analyze_array(self, image_array: np.ndarray, confidence_threshold: float = 0.8) -> int:
        """
        Анализирует входной массив изображения и возвращает однозначный класс (0, 1, 2).

        Args:
            image_array (np.ndarray): Массив изображения.
            confidence_threshold (float): Порог уверенности (по умолчанию 0.6).

        Returns:
            int: Класс (0, 1, 2), соответствующий предсказанию модели.
        """
        results = self.model(image_array, save=False)

        if len(results[0].boxes) == 0:
            return -1

        # Фильтрация по confidence_threshold
        valid_boxes = [
            box for box in results[0].boxes
            if box.conf.cpu().item() >= confidence_threshold
        ]

        if not valid_boxes:
            return 2  # Нет предсказаний выше порога -> здоровый зуб

        best_box = max(valid_boxes, key=lambda b: b.conf.cpu().item())
        return int(best_box.cls.cpu().item())


model_path = Path("neiro/models/kaif_caries.pt")
caries_model = Caries(model_path)

# img = image_to_numpy("D:\\PycharmProjects\\TgBotSbor\\photos\\results_pipe_1.jpg")
#
# print(caries_model.analyze_array(img))