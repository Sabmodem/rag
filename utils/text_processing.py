import hashlib
import re
from typing import Optional


def get_short_hash(text: str, length: int = 8) -> str:
    """Генерирует MD5 хэш заданной длины."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:length]


def format_chunk_output(
    chunk_text: str,
    metadata: dict,
    public_url_base: str,
    score: Optional[float] = None
) -> str:
    """
    Форматирует чанк и изображения для передачи в LLM.
    Заменяет относительные ссылки на публичные URL.
    """
    doc_hash = metadata.get("doc_hash", "N/A")
    file_name = metadata.get("file_name", "N/A")
    file_path = metadata.get("file_path", "N/A")
    image_names = metadata.get("image_paths", []) or metadata.get("image_urls", [])

    score_str = f" | Score: {score:.4f}" if score is not None else ""
    header = f"=== [Файл: {file_name} | doc_hash: {doc_hash}{score_str}] ==="

    base_url = public_url_base.rstrip('/')

    # 1. Исправляем относительные ссылки на картинки внутри текста чанка
    inline_img_regex = re.compile(r'!\[(.*?)\]\((.*?)\)')

    def replace_inline_url(match: re.Match) -> str:
        alt_text = match.group(1)
        filename = match.group(2)
        url = filename if filename.startswith("http") else f"{base_url}/{filename}"
        return f"![{alt_text}]({url})"

    processed_chunk_text = inline_img_regex.sub(replace_inline_url, chunk_text)

    # 2. Формируем отдельный блок прикрепленных изображений
    images_block = ""
    if image_names:
        formatted_imgs = []
        for img in image_names:
            img_url = img if img.startswith("http") else f"{base_url}/{img}"
            formatted_imgs.append(f"![{img}]({img_url})")
        images_block = "\n\n**Прикрепленные изображения:**\n" + "\n".join(formatted_imgs)

    return f"{header}\nПуть: {file_path}\n\nТекст:\n{processed_chunk_text}{images_block}\n"