import os
from dataclasses import dataclass, field
from typing import List, Tuple
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
from ultralytics import YOLO
from neiro import Tooth, MouthImage
from .transform import image_to_numpy


class SingleTooth:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise ValueError(f"Can't find model with path {model_path}")
        self.model = YOLO(model_path)
        self.names = self.model.names
        print(f"Model loaded with classes: {self.names}")

    def analyze(self, mouth_image: MouthImage, conf_threshold: float = 0.2) -> None:
        """
        Анализирует изображение из экземпляра MouthImage, добавляет боксы в поле boxes.

        Args:
            mouth_image (MouthImage): Экземпляр MouthImage с изображением для анализа.
            conf_threshold (float): Порог уверенности для боксов.
        """
        results = self.model(mouth_image.array, save=False)

        for box in results[0].boxes:
            xyxy = box.xyxy.cpu().numpy().astype(int)[0]  # [x_min, y_min, x_max, y_max]
            conf = box.conf.cpu().item()

            if conf >= conf_threshold:
                # Вырезаем область изображения
                cropped = mouth_image.array[xyxy[1]:xyxy[3], xyxy[0]:xyxy[2]]
                if cropped.size > 0:
                    mouth_image.boxes.append(Tooth(tooth_array=cropped, tooth_coord=xyxy.tolist()))

    def save_boxes(self, mouth_image: MouthImage, output_folder: str, drawn_image_path: str):
        """
        Сохраняет исходное изображение с размеченными боксами и каждый бокс отдельно.

        Args:
            mouth_image (MouthImage): Экземпляр MouthImage с заполненными боксами.
            output_folder (str): Папка для сохранения вырезанных боксов.
            drawn_image_path (str): Путь для сохранения изображения с размеченными боксами.
        """
        print(f"Output folder: {output_folder}")
        print(f"Drawn image path: {drawn_image_path}")
        print(f"Number of boxes: {len(mouth_image.boxes)}")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        try:
            drawn_image = Image.fromarray(mouth_image.array).convert("RGB")
        except Exception as e:
            print(f"Error converting image array to Image: {e}")
            return

        draw = ImageDraw.Draw(drawn_image)

        for i, tooth in enumerate(mouth_image.boxes):
            try:
                draw.rectangle(tooth.tooth_coord, outline="red", width=3)
                box_image = Image.fromarray(tooth.tooth_array)
                box_path = os.path.join(output_folder, f"box_{i + 1}.jpg")
                box_image.save(box_path)
                print(f"Saved box {i + 1} to {box_path}")
            except Exception as e:
                print(f"Error saving box {i + 1}: {e}")

        try:
            drawn_image.save(drawn_image_path)
            print(f"Saved image with drawn boxes to {drawn_image_path}")
        except Exception as e:
            print(f"Error saving drawn image: {e}")


# Пример использования
model_path = Path("neiro/models/yolov8x_merged_dataset_best.pt")
single_tooth_model = SingleTooth(model_path)

# image_path = "../photos/0.95_Lower_2023-08-24-10-05-05_Lower_jpg.jpg"
# output_boxes_folder = "./photos/cropped_boxes"
# output_drawn_path = "./photos/drawn_boxes.jpg"
#
# image_array = image_to_numpy(image_path)
# mouth_image = MouthImage(array=image_array, mouth_type="Lower")
#
# single_tooth_model.analyze(mouth_image, conf_threshold=0.5)
# single_tooth_model.save_boxes(mouth_image, output_boxes_folder, output_drawn_path)