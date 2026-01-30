from datetime import datetime
import math
from io import BytesIO
import os

from pathlib import Path
from pathvalidate import sanitize_filepath
import requests
from PIL import Image

from Config import config

class PicArchive:
    async def save(self, username: str, url: str) -> str | None:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            is_portrait = img.height > img.width
            aspect_ratio = img.height / img.width if is_portrait else img.width / img.height
            small_side = int(config.settings["pics"]["size"])
            large_side = int(small_side * aspect_ratio)
            margin = int((large_side - small_side) / 2)

            if is_portrait:
                img = img.resize((small_side, large_side), Image.Resampling.LANCZOS)
                img = img.crop((0, margin, small_side, small_side + margin))
            else:
                img = img.resize((533, 400), Image.Resampling.LANCZOS)
                img = img.crop((margin, 0, small_side + margin, small_side))

            subfolder_path = os.path.join(config.settings["pics"]["root_folder"], sanitize_filepath(username))
            os.makedirs(subfolder_path, exist_ok=True)
            filename = os.path.join(subfolder_path, datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) + ".webp"

            img.save(filename)
            print(f"Saved pic to {filename}")

            return filename
        else:
            print("Couldn't retrieve pic: {url}")
            return None

    def make_collage(self, username) -> Image.Image | None:
        directory = os.path.join(config.settings["pics"]["root_folder"], username)

        if Path(directory).exists():
            pics = os.listdir(directory)

            if len(pics) == 0:
                return None

            grid_size = math.ceil(math.sqrt(len(pics)))
            size = int(config.settings["pics"]["size"])
            full_image_size = size * grid_size
            merged_image = Image.new('RGB', (full_image_size, full_image_size), (50,51,56))

            x = 0
            y = 0

            for pic in pics:
                try:
                    img = Image.open(directory + "/" + pic)
                    merged_image.paste(img, (x * size, y * size))

                    x +=1

                    if x == grid_size:
                        x = 0
                        y += 1
                except Exception as e:
                    print(f"Couldn't process pic {directory + "/" + pic}: {e}")

            last_row_with_content = y if x > 0 else y-1

            merged_image = merged_image.crop((0,0, full_image_size, (last_row_with_content + 1) * size))

            return merged_image
        else:
            return None
