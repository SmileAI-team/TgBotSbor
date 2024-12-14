import os
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from PIL import Image
from typing import Tuple, Union, List

from transform import image_to_numpy, save_image_from_numpy
from neiro import MouthImage


class CutMouthModel:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise ValueError(f"Can't find model with path {model_path}")
        self.model = YOLO(model_path)
        self.names = self.model.names
        print(f"Model loaded with classes: {self.names}")

    def analyze(self, image_array: np.ndarray, confidence_threshold: float = 0.6) -> Tuple[
        bool, Union[np.ndarray, None], Union[str, None]]:

        mouth_types = {0: 'Front view', 1: 'Lower Jaw', 2: 'Upper Jaw'}

        image = Image.fromarray(image_array)

        results = self.model(image, save=False)
        detections = results[0].boxes

        if len(detections) == 0:
            return False, None, None

        best_detection = detections.data[0]
        confidence = best_detection[4]

        if confidence < confidence_threshold:
            return False, None, None

        n = 25
        x_min = max(0, int(best_detection[0]) - n)
        y_min = max(0, int(best_detection[1]) - n)
        x_max = min(image.width, int(best_detection[2]) + n)
        y_max = min(image.height, int(best_detection[3]) + n)

        cropped_image = image.crop((x_min, y_min, x_max, y_max))

        cropped_array = np.array(cropped_image)

        mouth_type_index = int(best_detection[5])
        mouth_type = mouth_types.get(mouth_type_index, "Unknown")

        return True, cropped_array, mouth_type


model_path = Path("../models/TEMP_VAR.pt")
cut_mouth_model = CutMouthModel(model_path)


def cut_images(list_images: List):
    datacls_list = []
    error = None
    exit_code = True

    for index, arr_img in enumerate(list_images):
        exit_code, result_array, mouth_type = cut_mouth_model.analyze(arr_img)

        if not exit_code:
            error = f"Фото {index + 1} не верно"
            return False, error, None

        if datacls_list:
            for datacls in datacls_list:
                if datacls.mouth_type == mouth_type:
                    error = f"Фотографии одного типа: {mouth_type}"
                    return False, error, None

        image = MouthImage(
            array=result_array,
            mouth_type=mouth_type,
            boxes=[],
            caries_coord=[])

        datacls_list.append(image)

    return exit_code, error, datacls_list

