import math
from io import BytesIO
import os

from pathlib import Path
from pathvalidate import sanitize_filepath
import requests
from PIL import Image, ImageDraw, ImageFont

from Config import config
from Logic import Logic

class PicArchive:
    logic: Logic

    def __init__(self, logic: Logic):
        self.logic = logic

    async def save(self, username: str, url: str, title: str) -> str | None:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            try:
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
                    img = img.resize((large_side, small_side), Image.Resampling.LANCZOS)
                    img = img.crop((margin, 0, small_side + margin, small_side))

                subfolder_path = os.path.join(config.settings["pics"]["root_folder"], sanitize_filepath(username))
                os.makedirs(subfolder_path, exist_ok=True)
                filename = os.path.join(subfolder_path, title) + ".webp"

                img.save(filename)
                print(f"Saved pic to {filename}")

                return filename
            except Exception as e:
                print(f"Couldn't process pic {url}: {e}")
        else:
            print("Couldn't retrieve pic {url}")
            return None

    def make_collage(self, username) -> Image.Image | None:
        pics = self.get_pics_for_user(username)

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
                merged_image.paste(pic, (x * size, y * size))

                x +=1

                if x == grid_size:
                    x = 0
                    y += 1
            except Exception as e:
                print(f"Couldn't process pic {pic.filename}: {e}")

        last_row_with_content = y if x > 0 else y-1

        merged_image = merged_image.crop((0,0, full_image_size, (last_row_with_content + 1) * size))

        return merged_image

    def make_board(self, scores: dict[str, int]) -> Image.Image | None:
        scores = {self.logic.denormalize_name(key): value for key, value in scores.items()}

        max_pics = max(list(map(self.get_number_of_pics_for_user, scores.keys())))

        height = len(scores.items())
        width = max_pics + 2

        largest_dim = height if height > width else width
        native_size = int(config.settings["pics"]["size"])
        size = native_size

        resolution_limit = int(config.settings["pics"]["max_board_size"]) or None
        projected_image_resolution = height * native_size * width * native_size

        # WebP images can only be up to 16383px a side, and Discord won't embed anything larger than 90250000px in total.
        # You can also specify a lower maximum in the config file.
        if resolution_limit is not None and projected_image_resolution > resolution_limit:
            size = math.floor(math.sqrt(resolution_limit)/math.sqrt(height * width))
            print(f"Resized pics from {native_size}px to {size}px (user limitation)")

        projected_image_resolution = height * size * width * size

        if largest_dim * size > 16383 or projected_image_resolution > 90250000:
            webp_size = math.floor(16383/largest_dim)
            discord_size = math.floor(9500/math.sqrt(height * width))

            size = webp_size if webp_size < discord_size else discord_size

            print(f"Resized pics from {native_size}px to {size}px (webp or discord limitation)")

        image = Image.new('RGB', (width * size, height * size), (50,51,56))
        draw = ImageDraw.Draw(image)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size * 0.25))
        score_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(size * 0.25))

        margin = int(size/2.25)

        name_index = 0

        for name in scores.keys():
            draw.text(xy=(int(margin/4), name_index * size + margin - int(margin/3)), text=self.logic.normalize_name(name), font=name_font, fill=(255,255,255))
            draw.text(xy=(int(margin/4), name_index * size + margin + int(margin/3)), text=str(scores[name]), font=score_font, fill=(255,255,255))

            pics = self.get_pics_for_user(name)

            image_index = 2
            for pic in pics:
                if native_size != size:
                    pic = pic.resize((size, size))
                image.paste(pic, (image_index * size, name_index * size))
                image_index += 1
            name_index += 1

        return image

    def get_pics_for_user(self, username: str):
        directory = os.path.join(config.settings["pics"]["root_folder"], username)
        if Path(directory).exists():
            pics = os.listdir(directory)
            pics.sort()
            for pic in pics:
                yield Image.open(directory + "/" + pic)

    def get_number_of_pics_for_user(self, username: str) -> int:
        directory = os.path.join(config.settings["pics"]["root_folder"], username)
        if Path(directory).exists():
            return len(os.listdir(directory))
        else:
            return 0
