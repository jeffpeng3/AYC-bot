from functools import partial
from PIL import ImageFont
from PIL.Image import Image, new, open
from pilmoji import Pilmoji
from jieba import lcut
from PIL.ImageFilter import GaussianBlur
from PIL.ImageDraw import Draw

FONT_SIZE = 50


def get_icon_mask() -> Image:
    mask = new("L", (400, 400), 0)
    drawObj = Draw(mask)
    drawObj.ellipse((-400, -250, 350, 1300), fill=(255,))
    mask = mask.filter(GaussianBlur(radius=25))
    mask = mask.resize((720, 720))

    return mask


mask = get_icon_mask()
font_path = "./NotoSans.ttf"
font = ImageFont.truetype(font_path, size=FONT_SIZE)
line_height = int(FONT_SIZE * 1.25)
getsize = partial(font.getlength)



def mask_icon(image: Image) -> Image:
    image.putalpha(mask)
    return image


def wrap_text(text: str, max_width: int) -> list[str]:
    strings = map(lcut,text.split("\n")) # type: ignore
    lines = []

    def merge_words(words):
        return "".join(words)

    for string in strings:
        current_line = []
        current_width = 0

        for word in string:
            word_size = getsize(word)
            if current_width + word_size > max_width:
                lines.append(merge_words(current_line))
                current_line = []
                current_width = 0
            current_line.append(word)
            current_width += word_size

        if current_line:  # 加入最後一行
            lines.append(merge_words(current_line))
    print(lines)

    return lines


def create_text_image(
    text: str,
) -> Image:
    """生成純文字圖片，寬度為高度的1.5倍，並返回文字排版資訊"""
    height = 720
    width = 936
    text_width = int(width * 0.95)
    text_p = int(width * 0.05)
    text_layer = new("RGBA", (width, height), (0,0,0, 0))

    with Pilmoji(text_layer) as pilmoji:
        lines = wrap_text(text, text_width)

        total_height = line_height * len(lines)
        start_y = int((height - total_height) / 2)
        line_widths = map(lambda line: (line, getsize(line)), lines)

        # 繪製每一行文字（在置中的區塊內靠左對齊）
        for idx, (text, length) in enumerate(line_widths):
            y = int(start_y + idx * line_height)  # 轉換為整數
            x = int((width - length - text_p) / 2)

            emoji_offset = 20
            pilmoji.text(
                (x, y),
                text,
                font=font,
                align="center",
                fill=(255,255,255),
                emoji_scale_factor=1.0,
                emoji_position_offset=(0, emoji_offset),
            )

    return text_layer


def concatenate_images(
    left_image: Image,
    text_image: Image,
    output_path: str = "output.jpg",
) -> None:
    final_image = new("RGBA", (1656, 720), (0,0,0, 255))
    final_image.paste(text_image, (720, 0), text_image)
    final_image.paste(left_image, (0, 0), left_image)
    final_image.convert("RGB").save(output_path)


def get_avatar():
    with open("img.png") as avatar:
        avatar = avatar.resize((720, 720))
        avatar = avatar.convert("RGBA")
    return avatar


if __name__ == "__main__":
    sample_text = """Hello🤣這是一個
😂測試Hello🤣這是一試Hello🤣這是一個😂測試文字😍🥰
fffffffff
🥰
sdf"""
    print(sample_text)
    text_image = create_text_image(sample_text)

    avatar = get_avatar()
    avatar = mask_icon(avatar)
    avatar.save("avatar.png")
    print("圓形圖標已生成：avatar.png")

    # 步驟 1: 生成文字圖片
    print("文字圖片已生成")
    text_image.save("text.png")
    # 步驟 2: 拼接圖片
    concatenate_images(avatar, text_image)
    print("拼接圖片已生成：output.jpg")


"""
|生成|config 1|config2|......|
|config 1|
|生成|config 1|config2|......|
|config 2|
|生成|config 1|config2|......|
|config 3|
|生成|config 1|config2|......|
"""