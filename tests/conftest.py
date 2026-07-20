import pytest


@pytest.fixture
def sample_metadata():
    return {
        "doc_hash": "a1b2c3d4",
        "file_name": "test_doc.md",
        "file_path": "/docs/test_doc.md",
        "image_paths": ["img1.png", "img2.png"]
    }


@pytest.fixture
def sample_chunk_text():
    return (
        "Это фрагмент текста с картой схемы.\n\n"
        "![Схема объекта](images/scheme.png)\n\n"
        "Продолжение описания правил монтажа."
    )