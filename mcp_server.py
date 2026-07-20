import logging
from typing import Optional
from fastmcp import FastMCP

from config import settings
from services.vector_store import QdrantService
from services.search_engine import RAGSearchEngine
from utils.text_processing import format_chunk_output

logger = logging.getLogger(__name__)

# Инициализируем FastMCP
mcp = FastMCP("RAG-Knowledge-Base-MCP")

# Глобальные контейнеры для сервисов (инициализируются при запуске)
qdrant_service: Optional[QdrantService] = None
search_engine: Optional[RAGSearchEngine] = None


def init_services():
    """Ленивая инициализация тяжелых сервисов."""
    global qdrant_service, search_engine
    if search_engine is None:
        logger.info("Инициализация поискового движка и подключений...")
        qdrant_service = QdrantService()
        search_engine = RAGSearchEngine(qdrant_service=qdrant_service)


@mcp.tool()
def search_knowledge_base(
    query_text: str,
    top_k_candidates: int = 30,
    top_n_final: int = 5
) -> str:
    """
    Семантический поиск по базе знаний с переранжированием через Reranker.
    
    Args:
        query_text: Текст запроса или вопроса.
        top_k_candidates: Количество первичных кандидатов из вектора (по умолчанию 30).
        top_n_final: Итоговое количество самых релевантных чанков (по умолчанию 5).
    """
    init_services()
    return search_engine.search(
        query_text=query_text,
        top_k_candidates=top_k_candidates,
        top_n_final=top_n_final
    )


@mcp.tool()
def get_document_chunks_by_hash(doc_hash: str, limit: int = 100) -> str:
    """
    Получение всех чанков, принадлежащих одному документу по его doc_hash.
    Полезно, если нужно прочитать документ целиком.

    Args:
        doc_hash: Хэш-идентификатор документа (берется из метаданных найденного чанка).
        limit: Максимальное количество чанков для выдачи (по умолчанию 100).
    """
    init_services()
    raw_chunks = qdrant_service.get_chunks_by_doc_hash(doc_hash=doc_hash, limit=limit)

    if not raw_chunks:
        return f"Чанков с doc_hash='{doc_hash}' не найдено."

    chunks_output = []
    for idx, payload in enumerate(raw_chunks, 1):
        text = payload.get("text", "")
        formatted = format_chunk_output(
            chunk_text=text,
            metadata=payload,
            public_url_base=settings.minio_public_url
        )
        chunks_output.append(f"[Фрагмент #{idx}]\n{formatted}")

    return f"Найдено чанков для doc_hash '{doc_hash}': {len(raw_chunks)}\n\n" + "\n\n".join(chunks_output)


if __name__ == "__main__":
    init_services()
    mcp.run(transport='sse', host='0.0.0.0', port=8000)