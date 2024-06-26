import os
import io
import tempfile
import uuid
from pathlib import Path
from datetime import datetime
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import List, Union

from core.models.items import Items
from core.models.user import Users
from items.crud import create_item
from user.crud import get_user_by_telegram_id
from items.schemas import ItemCreate
from google_drive import create_folder, upload_file
from ultralytics import YOLO
from torchvision import transforms

class CutMouthModel:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise ValueError(f"Can't get model with path {model_path}")
        self.model = YOLO(model_path)
        self.names = {0: 'Front view', 1: 'Lower Jaw', 2: 'Upper Jaw'}
        print(self.names)

    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        resized_image = image.resize((640, 640))  # Пример изменения размера до 640x640
        return resized_image

    @staticmethod
    def open_image_from_bytes(file: io.BytesIO) -> Image.Image:
        file.seek(0)
        im = Image.open(file)
        preprocessed_image = CutMouthModel.preprocess_image(im)
        return preprocessed_image

    async def analyze(self, photo_bytes: io.BytesIO, original_filename: str, save_path: Path):
        if isinstance(photo_bytes, bytes):
            photo_bytes = io.BytesIO(photo_bytes)

        photo = self.open_image_from_bytes(photo_bytes)
        transform = transforms.Compose([
            transforms.ToTensor()
        ])
        photo_tensor = transform(photo).unsqueeze(0)

        result = self.model(photo_tensor)[0]
        boxes = result.boxes

        if len(boxes) == 0:
            return False, "Mouth not detected", None

        elem = boxes[0]
        image = Image.open(photo_bytes)

        n = 25
        print(self.names[int(elem.cls[0])])

        label_name = self.names[int(elem.cls[0])].split()[0]

        with tempfile.TemporaryDirectory() as tmpdirname:
            save_file_name = Path(tmpdirname) / f"{label_name}_{original_filename}"
            image.save(save_file_name)

            with open(save_file_name, "rb") as img_file:
                result_image_bytes = io.BytesIO(img_file.read())

        return True, result_image_bytes, label_name


async def process_files(telegram_id: str, files: List[Union[io.BytesIO, bytes]], comment: str, db: AsyncSession):
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now()
    folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")

    if user.google_path.startswith('https://drive.google.com/drive/folders/'):
        parent_folder_id = user.google_path.split('/')[-1]
    else:
        raise HTTPException(status_code=500, detail="Invalid google_path format")

    model_path = "TEMP_VAR.pt"  # Путь к вашей модели
    model = CutMouthModel(model_path)

    verified_files = []

    for i, file in enumerate(files):
        if isinstance(file, bytes):
            file = io.BytesIO(file)

        file_name = f"file_{uuid.uuid4()}.jpg"

        success, result_image_bytes, label = await model.analyze(file, file_name, Path("/tmp"))
        if not success:
            return {"detail": f"Mouth not detected on photo number {i + 1}"}

        verified_files.append((label, result_image_bytes, file_name))

    folder_url = await create_folder(folder_name, parent_folder_id)
    folder_id = folder_url.split('/')[-1]

    for label, result_image_bytes, original_filename in verified_files:
        result_image_bytes.seek(0)
        file_name = f"{label}_{original_filename}.jpg"
        await upload_file(file_name=file_name, folder_id=folder_id, file_content=result_image_bytes)

    # Создаем запись в базе данных
    item = ItemCreate(
        user_id=user.id,
        time=now,
        google_drive_path=f"https://drive.google.com/drive/folders/{folder_id}",
        viewed=False,
        validated=False,
        comment=comment
    )
    await create_item(db, item)

    return {"detail": "Success"}
