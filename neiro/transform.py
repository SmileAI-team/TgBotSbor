import base64
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import json
from dataclasses import asdict, is_dataclass


def image_to_numpy(image_path):

    image_path = Path(image_path)
    image = Image.open(image_path)

    # Конвертируем изображение в формат RGB, если необходимо
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Преобразуем изображение в NumPy массив
    image_array = np.array(image)

    return image_array


def save_image_from_numpy(image_array, filename):
    save_dir = Path("./results")
    save_path = Path(save_dir) / filename

    image = Image.fromarray(image_array.astype(np.uint8))

    image.save(str(save_path), format="JPEG")

    print(f"Изображение сохранено: {save_path}")

def custom_asdict(obj):
    """
    Рекурсивное преобразование датакласса в сериализуемый словарь.
    Преобразует `numpy.ndarray` в список.
    """
    if is_dataclass(obj):
        # Если объект является датаклассом, преобразуем его в словарь
        return {key: custom_asdict(value) for key, value in asdict(obj).items()}
    elif isinstance(obj, np.ndarray):
        # Если объект — np.ndarray, преобразуем в список
        return obj.tolist()
    elif isinstance(obj, list):
        # Если объект — список, рекурсивно обрабатываем элементы
        return [custom_asdict(item) for item in obj]
    elif isinstance(obj, dict):
        # Если объект — словарь, рекурсивно обрабатываем ключи и значения
        return {key: custom_asdict(value) for key, value in obj.items()}
    else:
        # Возвращаем объект без изменений, если он не требует обработки
        return obj

def save_dataclass(dataclass_instance, output_path: str):
    """
    Сохраняет вложенный датакласс в формате JSON.

    Args:
        dataclass_instance: Экземпляр датакласса для сохранения.
        output_path (str): Путь к выходному JSON-файлу.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Преобразуем датакласс в сериализуемый формат
        serialized_data = custom_asdict(dataclass_instance)
        # Сохраняем в JSON с отступами для удобного просмотра
        json.dump(serialized_data, f, ensure_ascii=False, indent=4)

def decode_base64_to_image(encoded_image: str) -> np.array:
    """Декодирует изображение из base64 в numpy-массив."""
    image_data = base64.b64decode(encoded_image)
    image_array = np.frombuffer(image_data, np.uint8)
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)