import argparse
import multiprocessing
from pathlib import Path

from config import settings
from converters.html_converter import HtmlConverter
from ingestion.pipeline import IngestionPipeline, IngestionConfig
from services.minio_service import MinioService
from services.vector_store import QdrantService
from services.search_engine import RAGSearchEngine


def main():
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="Полный пайплайн: Конвертация HTML -> Markdown -> Qdrant")
    parser.add_argument("--input-dir", type=str, default=str(settings.docs_dir), help="Директория с документами")
    parser.add_argument("--chunk-size", type=int, default=1024, help="Размер чанка")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Перекрытие чанков")
    parser.add_argument("--skip-html", action="store_true", help="Пропустить этап конвертации HTML -> MD")
    args = parser.parse_args()

    docs_path = Path(args.input_dir)

    # 1. Проверка бакета MinIO
    print("Проверка подключения к MinIO...")
    minio_service = MinioService()
    minio_service.ensure_bucket_exists()

    # 2. Конвертация HTML -> MD
    if not args.skip_html:
        print("\n--- Этап 1: Конвертация HTML в Markdown ---")
        try:
            converter = HtmlConverter()
            success, skipped = converter.convert_directory(docs_path)
            print(f"Конвертация завершена. Успешно: {success}, Пропущено (уже были): {skipped}")
        except Exception as e:
            print(f"Ошибка при конвертации HTML: {e}")

    # 3. Индексация в Qdrant
    print("\n--- Этап 2: Параллельная индексация документов в Qdrant ---")
    qdrant_service = QdrantService()
    search_engine = RAGSearchEngine(qdrant_service=qdrant_service)
    
    ingestion_config = IngestionConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    pipeline = IngestionPipeline(
        qdrant_service=qdrant_service,
        search_engine=search_engine,
        config=ingestion_config
    )

    pipeline.run(input_dir=docs_path, recreate_collection=True)
    print("\n Вся обработка успешно завершена!")


if __name__ == "__main__":
    main()