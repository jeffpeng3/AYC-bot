from discord import Message
from google.genai.types import (
    Part,
    Blob,
)
from core.shared import get_client
from typing import List, Tuple
import re

MAX_LENGTH = 2000
CODE_BLOCK_LANG = "python"
MIN_CHUNK_SIZE = 200
MERGE_THRESHOLD = 1000
SMALL_CHUNK_THRESHOLD = 100
LOOK_AHEAD = 20
CODE_BLOCK_END_SAVE = 10
PREFIX_TEXT_MIN_LENGTH = 100
PUNCTUATION = '。！？'
COMMA_PUNCTUATION = '，、；'
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MIME_TYPE_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


class MarkdownElement:
    def __init__(self, start: int, end: int, type: str):
        self.start = start
        self.end = end
        self.type = type

def find_code_blocks(text: str) -> List[Tuple[int, int]]:
    pattern = r'```[\s\S]*?```'
    return [(m.start(), m.end()) for m in re.finditer(pattern, text)]


def find_inline_elements(text: str) -> List[MarkdownElement]:
    elements = []
    patterns = {
        'inline_code': r'`[^`]+`',
        'bold': r'\*\*[^*]+\*\*',
        'italic': r'\*[^*]+\*',
        'link': r'\[[^\]]+\]\([^)]+\)',
    }

    for type, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            elements.append(MarkdownElement(match.start(), match.end(), type))

    return sorted(elements, key=lambda x: x.start)


async def split_markdown_text(text: str, max_length: int = MAX_LENGTH) -> List[str]:
    if len(text) <= max_length:
        return [text]

    code_blocks = find_code_blocks(text)
    inline_elements = find_inline_elements(text)

    chunks = []
    current_pos = 0

    while current_pos < len(text):
        in_code_block = False

        for start, end in code_blocks:
            if start > current_pos:
                break
            if start <= current_pos < end:
                block_text = text[start:end]
                if len(block_text) > max_length:
                    lines = block_text.split('\n')
                    current_chunk = []
                    current_length = 0

                    for line in lines:
                        if current_length + len(line) + 1 > max_length - CODE_BLOCK_END_SAVE:
                            chunk_text = f'```{CODE_BLOCK_LANG}\n' + '\n'.join(current_chunk) + '\n```'
                            chunks.append(chunk_text)
                            current_chunk = []
                            current_length = 0
                        current_chunk.append(line)
                        current_length += len(line) + 1

                    if current_chunk:
                        chunk_text = f'```{CODE_BLOCK_LANG}\n' + '\n'.join(current_chunk) + '\n```'
                        chunks.append(chunk_text)
                else:
                    if current_pos < start:
                        prefix_text = text[current_pos:start].rstrip()
                        if prefix_text and len(prefix_text) >= PREFIX_TEXT_MIN_LENGTH:
                            chunks.append(prefix_text)
                    chunks.append(block_text)
                current_pos = end
                in_code_block = True
                break

        if in_code_block:
            continue

        remaining_length = len(text) - current_pos

        if chunks and remaining_length <= MERGE_THRESHOLD:
            last_chunk = chunks[-1]
            if len(last_chunk) + remaining_length <= max_length:
                chunks[-1] = last_chunk + text[current_pos:]
                break

        if remaining_length <= max_length:
            chunks.append(text[current_pos:])
            break

        end_pos = min(current_pos + max_length, len(text))
        best_pos = end_pos

        for i in range(end_pos - 1, current_pos, -1):
            if i > 0 and text[i] == '\n' and text[i-1] == '\n':
                best_pos = i + 1
                break

        if best_pos == end_pos:
            for i in range(end_pos - 1, current_pos, -1):
                max_allowed_pos = current_pos + max_length
                if text[i] in PUNCTUATION:
                    if i + 1 <= max_allowed_pos and i + 1 - current_pos >= MIN_CHUNK_SIZE:
                        best_pos = i + 1
                        break
                elif text[i] == '\n' and i > 0 and text[i-1] == '\n':
                    if i + 1 <= max_allowed_pos and i + 1 - current_pos >= MIN_CHUNK_SIZE:
                        best_pos = i + 1
                        break
                elif text[i] in COMMA_PUNCTUATION:
                    if i + 1 <= max_allowed_pos and i + 1 - current_pos >= MIN_CHUNK_SIZE:
                        best_pos = i + 1
                        break

        if best_pos == end_pos:
            remaining = len(text) - current_pos

            if remaining <= MERGE_THRESHOLD and chunks:
                potential_merge = chunks[-1] + text[current_pos:]
                if len(potential_merge) <= max_length:
                    chunks[-1] = potential_merge
                    break

            if remaining <= max_length:
                best_pos = len(text)
            else:
                best_pos = current_pos + max_length
                if best_pos == end_pos:
                    best_pos = current_pos + max_length

            last_chunk_size = remaining - max_length
            if last_chunk_size < SMALL_CHUNK_THRESHOLD:
                max_length = remaining - SMALL_CHUNK_THRESHOLD

            temp_pos = current_pos + max_length
            while temp_pos > current_pos + max_length - LOOK_AHEAD and temp_pos > current_pos:
                if text[temp_pos] in f'{COMMA_PUNCTUATION}{PUNCTUATION}\n':
                    best_pos = temp_pos + 1
                    break
                temp_pos -= 1

            if best_pos == end_pos:
                if len(text) - (current_pos + max_length) < SMALL_CHUNK_THRESHOLD:
                    best_pos = len(text)
                else:
                    best_pos = current_pos + max_length

        for elem in inline_elements:
            if elem.start < best_pos < elem.end:
                best_pos = elem.start

        chunks.append(text[current_pos:best_pos])
        current_pos = best_pos
    return chunks


async def parse_message(message: Message) -> Part:
    prefix = f'<author>{message.author.display_name}({message.author.id})</author>\n<content>'
    postfix = '</content>'
    if message.author.bot:
        prefix = ''
        postfix = ''
    part = Part(text=f'{prefix}{message.content}{postfix}')
    for file in message.attachments:
        extension = file.filename.rsplit(".", 1)[-1].lower()
        if extension in IMAGE_EXTENSIONS:
            mime = MIME_TYPE_MAP[extension]
            async with (await get_client()).get(file.url) as response:
                image_raw = await response.read()
            part.inline_data = Blob(data=image_raw, mime_type=mime)
            break
    return part
