# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import base64
from io import BytesIO


def encode_image_from_url(image_url):
    from aworld.utils.import_package import import_package
    import_package("requests")

    import requests
    from PIL import Image

    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))

    max_size = 1024
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.LANCZOS)

    buffered = BytesIO()
    image_format = image.format if image.format else 'JPEG'
    image.save(buffered, format=image_format)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def encode_image_from_file(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()
