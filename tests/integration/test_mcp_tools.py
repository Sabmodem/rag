from unittest.mock import MagicMock, patch
import mcp_server


@patch("mcp_server.search_engine")
@patch("mcp_server.qdrant_service")
def test_search_knowledge_base_mcp_tool(mock_qdrant, mock_search_engine):
    mock_search_engine.search.return_value = "=== [Файл: test.md] ===\nНайденный текст"
    
    # Сначала вызываем init_services, а затем подменяем на моки
    mcp_server.init_services()
    mcp_server.search_engine = mock_search_engine
    mcp_server.qdrant_service = mock_qdrant

    result = mcp_server.search_knowledge_base(query_text="правила монтажа", top_k_candidates=10, top_n_final=2)

    assert "=== [Файл: test.md] ===" in result
    mock_search_engine.search.assert_called_once_with(
        query_text="правила монтажа",
        top_k_candidates=10,
        top_n_final=2
    )


def test_get_document_chunks_by_hash_not_found():
    mock_qdrant = MagicMock()
    mock_qdrant.get_chunks_by_doc_hash.return_value = []
    
    # Инициализируем и явно переопределяем
    mcp_server.init_services()
    mcp_server.qdrant_service = mock_qdrant

    result = mcp_server.get_document_chunks_by_hash(doc_hash="invalid_hash")

    assert "Чанков с doc_hash='invalid_hash' не найдено." in result
    mock_qdrant.get_chunks_by_doc_hash.assert_called_once_with(doc_hash="invalid_hash", limit=100)