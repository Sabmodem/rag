import multiprocessing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.schema import TextNode
from llama_index.readers.file import FlatReader
from llama_index.vector_stores.qdrant import QdrantVectorStore

from config import settings
from ingestion.image_processor import ImageProcessor
from services.minio_service import MinioService
from services.search_engine import RAGSearchEngine
from services.vector_store import QdrantService
from utils.text_processing import get_short_hash


@dataclass
class IngestionConfig:
    chunk_size: int = 1024
    chunk_overlap: int = 200
    batch_size: int = 512
    max_text_len: int = 100_000


def _worker_process_file_batch(batch_args: Tuple[List[str], int, int]) -> List[Dict[str, Any]]:
    """Функция-воркер для параллельного процесса (выполняет считывание и чункинг)."""
    file_paths, chunk_size, chunk_overlap = batch_args
    parser = MarkdownNodeParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    file_reader = FlatReader()
    
    # Внутри воркера создаем изолированные сервисы для S3
    minio_service = MinioService()
    img_processor = ImageProcessor(minio_service)
    
    batch_results = []

    for path_str in file_paths:
        try:
            doc = file_reader.load_data(Path(path_str))
            nodes = parser.get_nodes_from_documents(doc)
            file_dir = str(Path(path_str).parent)
            doc_hash = get_short_hash(path_str)

            for node in nodes:
                raw_text = node.get_content()
                clean_text, image_ids = img_processor.process_chunk_images(raw_text, path_str, file_dir)

                batch_results.append({
                    "text": clean_text,
                    "payload": {
                        "text": clean_text,
                        "doc_hash": doc_hash,
                        "file_path": path_str,
                        "file_name": Path(path_str).name,
                        "has_images": len(image_ids) > 0,
                        "image_paths": image_ids
                    }
                })
        except Exception as e:
            print(f"[Worker Error] Ошибка при обработке файла {path_str}: {e}")

    return batch_results


class IngestionPipeline:
    """Оркестратор подготовки документов и записи в векторную БД."""

    def __init__(
        self,
        qdrant_service: QdrantService,
        search_engine: RAGSearchEngine,
        config: IngestionConfig = IngestionConfig()
    ):
        self.qdrant_service = qdrant_service
        self.search_engine = search_engine
        self.config = config

    def _run_parallel_parsing(self, all_files: List[str]) -> List[Dict[str, Any]]:
        batches = [
            all_files[i:i + self.config.batch_size]
            for i in range(0, len(all_files), self.config.batch_size)
        ]
        worker_args = [(batch, self.config.chunk_size, self.config.chunk_overlap) for batch in batches]

        num_workers = min(12, max(1, multiprocessing.cpu_count() - 2))
        print(f"Запуск подготовки данных в {num_workers} процессах...")

        all_prepared_data = []
        with multiprocessing.Pool(processes=num_workers) as pool:
            for result in pool.imap_unordered(_worker_process_file_batch, worker_args):
                all_prepared_data.extend(result)
                print(f"Обработана пачка. Всего чанков готово: {len(all_prepared_data)}")

        return all_prepared_data

    def _create_llama_nodes(self, raw_data: List[Dict[str, Any]]) -> List[TextNode]:
        llama_nodes = []
        for item in raw_data:
            text = item["text"]
            payload = item["payload"]

            if len(text) > self.config.max_text_len:
                text = text[:self.config.max_text_len] + "\n...[Текст урезан]"
                payload["text"] = text

            # Важно: текст кладем БЕЗ префикса "passage:", так как он
            # автоматически добавляется на уровне embed_model
            node = TextNode(
                text=text,
                metadata=payload
            )
            node.excluded_embed_metadata_keys = ["file_path", "file_name", "image_paths", "has_images"]
            llama_nodes.append(node)

        return llama_nodes

    def run(self, input_dir: Path, recreate_collection: bool = True) -> VectorStoreIndex:
        """Запускает полный цикл: поиск файлов -> чункинг -> эмбеддинги -> запись в Qdrant."""
        if not input_dir.exists():
            raise FileNotFoundError(f"Директория {input_dir} не найдена.")

        all_files = [str(p) for p in input_dir.glob("**/*.md")]
        print(f"Найдено Markdown-файлов для индексации: {len(all_files)}")

        # 1. Многопроцессорная обработка
        prepared_data = self._run_parallel_parsing(all_files)

        # 2. Подготовка коллекции в Qdrant
        if recreate_collection:
            self.qdrant_service.recreate_collection()

        # 3. Подготовка VectorStore
        vector_store = QdrantVectorStore(
            collection_name=settings.collection_name,
            client=self.qdrant_service.client,
            batch_size=64
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # 4. Преобразование в ноды и индексация
        llama_nodes = self._create_llama_nodes(prepared_data)
        
        print("Генерация эмбеддингов и отправка нод в Qdrant...")
        index = VectorStoreIndex(
            nodes=llama_nodes,
            storage_context=storage_context,
            embed_model=self.search_engine.embed_model,
            show_progress=True
        )

        # 5. Восстановление порога индексации Qdrant (исправление бага старой версии)
        self.qdrant_service.update_indexing_threshold(threshold=20000)

        print(f"Успешно заиндексировано {len(llama_nodes)} нод в коллекцию '{settings.collection_name}'.")
        return index