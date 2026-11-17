# RAG Knowledge Base MCP

## Quick Start

```bash
# Development environment (Nix)
nix-shell

# Run services (Docker)
docker-compose up -d qdrant minio minio-init

# Run MCP server
uv run fastmcp run main.py --port 8000 --host 0.0.0.0 --transport sse
```

## Architecture

- **main.py**: FastMCP entrypoint with tools `search_knowledge_base`, `get_document_chunks_by_hash`
- **services/**: `vector_store.py` (Qdrant), `search_engine.py` (RAG with reranking), `minio_service.py`
- **ingestion/**: `pipeline.py` (document processing), `image_processor.py`
- **cli/**: `ingest.py` (CLI for adding docs), `search.py`
- **converters/**: `html_converter.py` with Lua filter `clean.lua`

## Commands

```bash
# Run tests
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v

# CLI usage
uv run python -m cli.ingest --docs-dir ./docs
uv run python -m cli.search --query "your question"
```

## Key Dependencies

- Qdrant (vector store, port 6333)
- MinIO (object storage for images, ports 9000/9001)
- Models: `intfloat/multilingual-e5-small` (embeddings), `BAAI/bge-reranker-v2-m3` (reranker)

## Environment Variables

Required at minimum:
- `QDRant_HOST`, `QDRant_PORT`, `COLLECTION_NAME`
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`
- `EMbed model`, `reranker` model names
- `DOCS_DIR`, `LUA_filter` path
