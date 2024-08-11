import json
import os
from typing import Any
from PIL import Image
from io import BytesIO




from io import BytesIO

def upload_image_to_folder(media_file_path: str="media", media_content=object) -> BytesIO:
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, media_file_path + "/" + media_content.filename)
    media_content.save(path)

    with Image.open(path) as image:
        new_size = (800, 600)
        image = image.resize(new_size)

        # Create a BytesIO object to hold the modified image
        output = BytesIO()
        image.save(output, format="JPEG")
        output.seek(0)

    return output



def download_image_from_folder(json_file_location: str, file_contents: dict[dict[str, Any]]) -> None:
    """This function saves json file object to local file system

    :param json_file_location: json file.

    :returns: None
    """

    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, json_file_location)
    with open(path, "w") as outfile:
        json.dump(file_contents, outfile)