import math
from io import BytesIO
from pilmoji import Pilmoji
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as img

# from core.shared import get_client
from asyncio import run

my_string = """
肏你媽, world! 👋 Here are some emojis: 🎨 🌊 😎
I also support Discord emoji: <:rooThink:596576798351949847>
"""
FONT_WIDTH = 20
SMALL_FONT_WIDTH = 13
MAX_LINES = 3

font = ImageFont.truetype("NotoSans.ttf", 24)


def wrap_text(text: str, width: int) -> list:
    text = text.replace("\r\n", "\n")
    lines = []
    for line in text.split("\n"):
        lines.extend(wrap(line, width))
    return lines




async def get_image(url: str) -> img:
    # client = await get_client()
    # async with client.get(url) as image:
    #     return Image.open(BytesIO(await image.read()))
    # with open("img.png", "rb") as f:
    return Image.open("img.png")

def smooth01(x: float) -> float:
    return math.sin(x * math.pi - math.pi / 2) / 2 + 0.5


def alpha_gradient(image: img, x_s: int, x_e: int) -> img:
    image = image.convert("RGBA")
    w, h = image.size
    img = Image.new("L", (w, h), 255)
    for x in range(x_s, x_e + 1):
        alpha = 255 - int(smooth01((x - x_s) / (x_e - x_s)) * 255)
        tmp_img = Image.new("L", (1, h), alpha)
        img.paste(tmp_img, (x, 0))

    image.putalpha(img)

    return image


async def generate_image(text: str, background: tuple, avatar_url: str) -> BytesIO:
    with Image.new("RGB", (1920, 1080), background) as image:
        with Pilmoji(image) as pilmoji:
            pilmoji.text((1000, 500), text, (0, 0, 0), font, align="center")

            avatar = await get_image(avatar_url)

            avatar = avatar.resize((1080, 1080))
            avatar = avatar.crop((324, 0, 1080, 1920))

            avatar = alpha_gradient(avatar, 540, 756)
            image.paste(avatar, (0, 0), avatar)

            text_wrapped = wrap_text(text, 18)
            y_min = 23
            y_max = 120
            # center vertically
            y_start = (y_max - y_min) / 2 - min(
                len(text_wrapped), MAX_LINES
            ) * FONT_WIDTH / 2
            y = int(y_start)
            x_start = 165
            x_end = 560
            i = 1
            if len(text_wrapped) > MAX_LINES:
                text_wrapped[MAX_LINES - 1] = text_wrapped[3][:-3] + "..."
            for line in text_wrapped:
                text_size = font.getlength(line)
                # center the text
                print(text_size)
                x = int(x_start + (x_end - x_start - text_size) / 2)
                pilmoji.text(
                    (x, y), line, font=font, fill=(0, 0, 0), embedded_color=True
                )
                y += FONT_WIDTH
                i += 1
            # left to right alpha gradient
            # draw avatar on the left
            # draw = ImageDraw.Draw(image)

            # x_center = 403
            # center user card
            # card_size = font_small.getsize("@"+reply.user_card)
            # x_card_start = x_center - card_size[0] / 2
            # draw.text((x_card_start, 95), "@"+reply.user_card, font=font_small, fill=(169, 172, 184, 255))

            # fmt_time = strftime("%Y年%m月%d日 %H点%M分", localtime(reply.time))
            # time_size = font_small.getsize(fmt_time)
            # x_time_start = x_center - time_size[0] / 2
            # draw.text((x_time_start, 115), fmt_time, font=font_small, fill=(169, 172, 184, 255))

        image.show()
        image_bytes = BytesIO()
        image.save(image_bytes, format="JPEG")
        image_bytes.seek(0)
        return image_bytes


run(generate_image(my_string, (255, 255, 255), "avatar_url: str"))
