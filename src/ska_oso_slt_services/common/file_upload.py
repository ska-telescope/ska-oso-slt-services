import json
import os
from typing import Any
from PIL import Image
from io import BytesIO


def upload_image_to_folder(media_file_path: str="media", file_id:str=None, media_content=object) -> BytesIO:
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, media_file_path + "/" + str(file_id) +"_" +media_content.filename)
    media_content.save(path)

    with Image.open(path) as image:
        new_size = (800, 600)
        image = image.resize(new_size)

        # Create a BytesIO object to hold the modified image
        output = BytesIO()
        image.save(output, format="JPEG")
        output.seek(0)
    return output, path



# def read_image_from_folder(json_file_location: str) -> bytes:
#     """This function saves json file object to local file system

#     :param json_file_location: json file.

#     :returns: bytes
#     """

#     cwd, _ = os.path.split(__file__)
#     path = os.path.join(cwd, json_file_location)

#     # Open the image file using a context manager
#     with Image.open(path) as image:
#         # Create a byte stream buffer
#         img_io = BytesIO()

#         # Save the image to the buffer in JPEG format
#         image.save(img_io, 'JPEG', quality=80)
#         img_io.seek(0)

#         return img_io.getvalue()

import base64

def read_image_from_folder(json_file_location: str) -> str:
    """
    This function reads an image file and returns its contents as a Base64-encoded string.

    :param json_file_location: Path to the image file.
    :return: Base64-encoded string representation of the image data.
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, json_file_location)

    with open(path, 'rb') as image_file:
        image_bytes = image_file.read()
        base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')

    return base64_encoded_image

    