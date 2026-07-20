import logging
from typing import List, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection_name = settings.collection_name

    def recreate_collection(self) -> None:
        """Удаляет коллекцию, если она существует."""
        if self.client.collection_exists(self.collection_name):
            logger.info(f"Удаление старой коллекции '{self.collection_name}'...")
            self.client.delete_collection(self.collection_name)

    def update_indexing_threshold(self, threshold: int = 20000) -> None:
        """Восстанавливает стандартный порог индексации Qdrant."""
        self.client.update_collection(
            collection_name=self.collection_name,
            optimizer_config=qmodels.OptimizersConfigDiff(
                indexing_threshold=threshold
            )
        )
        logger.info(f"Порог индексации Qdrant установлен на {threshold}.")

    def get_chunks_by_doc_hash(self, doc_hash: str, limit: int = 100) -> List[dict]:
        """Возвращает все чанки документа по его doc_hash."""
        scroll_result, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="doc_hash",
                        match=qmodels.MatchValue(value=doc_hash)
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        return [point.payload or {} for point in scroll_result]