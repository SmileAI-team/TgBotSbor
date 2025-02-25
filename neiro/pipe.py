import numpy as np

from neiro.cut_image import cut_mouth_model, cut_images
from neiro.single_tooth import single_tooth_model
from neiro.caries import caries_model
from neiro.transform import image_to_numpy, save_dataclass, save_image_from_numpy

from PIL import Image, ImageDraw
from typing import List
from pathlib import Path

# 0: "Обнаружен Кариес",
# 1: "Небольшое повреждение",
# 2: "Здоров "

# output_boxes_folder = Path("D:/PycharmProjects/TgBotSbor/photos/cropped_boxes")
# output_drawn_path = Path("D:/PycharmProjects/TgBotSbor/photos/drawn_boxes_7.jpg")
#
# test_image_1 = image_to_numpy("D:/PycharmProjects/TgBotSbor/photos/photo_2025-02-09_21-46-28.jpg")
# test_image_2 = image_to_numpy("D:/PycharmProjects/TgBotSbor/photos/photo_2025-02-12_16-41-48.jpg")
# test_image_3 = image_to_numpy("D:/PycharmProjects/TgBotSbor/photos/0.96_Lower_253_jpg.jpg")
# test_list = [test_image_1, test_image_2]


def pipeline_caries(list_images: List[np.ndarray]):
    result_list = []
    mouth_type = []
    result_dict = {}
    datacls_list = cut_images(list_images)

    for datacls in datacls_list:
        if datacls.mouth_type != 'Nah':
            single_tooth_model.analyze(datacls, conf_threshold=0.2)
            caries_model.analyze(datacls)
            image = Image.fromarray(datacls.array)
            draw = ImageDraw.Draw(image)
            type_of_image = datacls.mouth_type

            caries_count = {
                "type_0": 0,  # Количество кариеса типа 0
                "type_1": 0  # Количество кариеса типа 1
            }

            for caries in datacls.caries_coord:
                x_min, y_min, x_max, y_max = caries.caries_coord
                if caries.caries_type == 0:
                    color = "red"
                    caries_count["type_0"] += 1
                elif caries.caries_type == 1:
                    color = "blue"
                    caries_count["type_1"] += 1
                else:
                    continue
                draw.rectangle([x_min, y_min, x_max, y_max], outline=color, width=3)

            upd_img = np.array(image)
            result_list.append(upd_img)
            result_dict[type_of_image] = caries_count
        mouth_type.append(datacls.mouth_type)
        result_list.append(None)

    return mouth_type, result_list, result_dict

# def save_resylts(list_images: List[np.ndarray]):
#     for index, image in enumerate(list_images):
#         save_image_from_numpy(image, f"results_pipe_{index}.jpg")

#save_dataclass(datacls_list[1], Path("./photos/mouth_image_1.json"))



# mouth_type, result_list, result_dict = pipeline_caries(test_list)
# save_resylts(result_list)
# print(result_dict)
# print(mouth_type)

