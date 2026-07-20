from utils.text_processing import format_chunk_output, get_short_hash


def test_get_short_hash():
    text = "some_unique_string"
    hash_val = get_short_hash(text, length=8)
    
    assert len(hash_val) == 8
    assert isinstance(hash_val, str)
    # Повторный вызов должен давать один и тот же детерминированный результат
    assert get_short_hash(text, length=8) == hash_val


def test_format_chunk_output_replaces_inline_images(sample_chunk_text, sample_metadata):
    public_url = "http://phoenix.lan/images"
    formatted = format_chunk_output(
        chunk_text=sample_chunk_text,
        metadata=sample_metadata,
        public_url_base=public_url,
        score=0.9876
    )

    # Проверяем наличие заголовка и скора
    assert "=== [Файл: test_doc.md | doc_hash: a1b2c3d4 | Score: 0.9876] ===" in formatted
    
    # Проверяем подстановку публичного URL в inline markdown-картинку
    assert "![Схема объекта](http://phoenix.lan/images/images/scheme.png)" in formatted


def test_format_chunk_output_attached_images_block(sample_chunk_text, sample_metadata):
    public_url = "http://phoenix.lan/images"
    formatted = format_chunk_output(
        chunk_text=sample_chunk_text,
        metadata=sample_metadata,
        public_url_base=public_url
    )

    # Проверяем формирование отдельного блока прикрепленных картинок внизу
    assert "**Прикрепленные изображения:**" in formatted
    assert "![img1.png](http://phoenix.lan/images/img1.png)" in formatted
    assert "![img2.png](http://phoenix.lan/images/img2.png)" in formatted


def test_format_chunk_output_handles_empty_images():
    metadata = {
        "doc_hash": "12345678",
        "file_name": "empty.md",
        "file_path": "/docs/empty.md",
        "image_paths": []
    }
    chunk_text = "Чистый текст без картинок."
    formatted = format_chunk_output(
        chunk_text=chunk_text,
        metadata=metadata,
        public_url_base="http://localhost:9000"
    )

    assert "**Прикрепленные изображения:**" not in formatted
    assert "Чистый текст без картинок." in formatted