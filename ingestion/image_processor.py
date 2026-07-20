import os
import re
from pathlib import Path
from typing import List, Tuple
from services.minio_service import MinioService
from utils.text_processing import get_short_hash

IMG_REGEX = re.compile(r'!\[.*?\]\((.*?)\)')


class ImageProcessor:
    """Обработчик медиаданных в чанках Markdown."""

    def __init__(self, minio_service: MinioService):
        self.minio_service = minio_service

    def process_chunk_images(self, raw_text: str, doc_path: str, file_dir: str) -> Tuple[str, List[str]]:
        """
        Находит картинки в тексте чанка, загружает их в MinIO и 
        заменяет ссылки на плейсхолдеры вида ![filename](filename).
        """
        found_images = IMG_REGEX.findall(raw_text)
        if not found_images:
            return raw_text, []

        processed_image_names: List[str] = []

        for img_rel_path in found_images:
            short_id = get_short_hash(f"{doc_path}///{img_rel_path}")
            ext = os.path.splitext(img_rel_path)[1] or ".png"
            object_name = f"{short_id}{ext}"
            
            source_img_path = Path(file_dir) / img_rel_path

            if source_img_path.exists():
                uploaded_url = self.minio_service.upload_image(source_img_path, object_name)
                if uploaded_url:
                    processed_image_names.append(object_name)

        def replace_match(match: re.Match) -> str:
            orig_path = match.group(1)
            short_id = get_short_hash(f"{doc_path}///{orig_path}")
            ext = os.path.splitext(orig_path)[1] or ".png"
            filename = f"{short_id}{ext}"
            return f"![{filename}]({filename})"

        clean_text = IMG_REGEX.sub(replace_match, raw_text)
        return clean_text, processed_image_names