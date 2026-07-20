from unittest.mock import MagicMock
from ingestion.image_processor import ImageProcessor


def test_process_chunk_images_no_images():
    mock_minio = MagicMock()
    processor = ImageProcessor(minio_service=mock_minio)

    raw_text = "Простой текст без картинок"
    clean_text, image_names = processor.process_chunk_images(raw_text, "doc.md", "/path")

    assert clean_text == raw_text
    assert image_names == []
    mock_minio.upload_image.assert_not_called()


def test_process_chunk_images_with_missing_files():
    mock_minio = MagicMock()
    processor = ImageProcessor(minio_service=mock_minio)

    raw_text = "Текст с несуществующей картинкой ![alt](non_existent.png)"
    clean_text, image_names = processor.process_chunk_images(raw_text, "doc.md", "/non_existent_path")

    # Имя файла заменяется на short hash + расширение (.png)
    assert "![" in clean_text and ".png]" in clean_text
    # Так как файла физически нет на диске, загрузка в MinIO не вызывается и список загруженных пуст
    assert image_names == []
    mock_minio.upload_image.assert_not_called()