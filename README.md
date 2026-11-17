# RAG Knowledge Base MCP

A FastMCP-based RAG (Retrieval-Augmented Generation) server for semantic search over documents with image support.

## Features

- Semantic search with multilingual support
- Reranking with BGE Reranker for improved relevance
- Image handling via MinIO object storage
- Document ingestion pipeline with HTML/Lua filtering
- MCP protocol for LLM integration

## Quick Start

### Development Setup

```bash
# Enter Nix development shell
nix-shell

# Start required services
docker-compose up -d qdrant minio minio-init

# Run the MCP server
uv run fastmcp run main.py --port 8000 --host 0.0.0.0 --transport sse
```

### Environment Variables

Set the following in your environment or `.env` file:

```bash
# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
COLLECTION_NAME=construction_rules

# MinIO
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadminpassword
MINIO_BUCKET=rag-images
MINIO_PUBLIC_URL=http://phoenix.lan/images

# ML Models
EMBED_MODEL_NAME=intfloat/multilingual-e5-small
RERANKER_MODEL_NAME=BAAI/bge-reranker-v2-m3

# Paths
DOCS_DIR=./docs
LUA_FILTER_PATH=clean.lua
```

## Usage

### Ingest Documents

```bash
uv run python -m cli.ingest --docs-dir ./docs
```

### Search (CLI)

```bash
uv run python -m cli.search --query "your question"
```

### MCP Server

The server exposes two tools:

1. **search_knowledge_base(query_text, top_k_candidates=30, top_n_final=5)**
   - Semantic search with reranking
   - Returns formatted relevant chunks

2. **get_document_chunks_by_hash(doc_hash, limit=100)**
   - Retrieve all chunks for a document
   - Useful for reading complete documents

### Docker Deployment

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f mcp
```

## Architecture

```
┌─────────────────┐
│  MCP Clients    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   main.py       │ (FastMCP entrypoint)
│   - Tools       │
└────────┬────────┘
         │
    ┌────┴────┬─────────┐
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌──────────┐
│ Qdrant│ │ MinIO  │ │ RAG      │
│Vector │ │ Images │ │ Search   │
│ Store │ │Storage │ │ Engine   │
└────────┘ └────────┘ └──────────┘
```

**Key Components:**

- **main.py**: FastMCP server with search and document retrieval tools
- **services/vector_store.py**: Qdrant client for vector operations
- **services/search_engine.py**: RAG pipeline with embeddings + reranking
- **services/minio_service.py**: S3-compatible image storage
- **ingestion/pipeline.py**: Document processing and chunking
- **ingestion/image_processor.py**: Image extraction and upload
- **converters/html_converter.py**: HTML to Markdown with Lua filter
- **cli/ingest.py**: CLI for document ingestion
- **cli/search.py**: CLI for testing searches

## Testing

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests (requires services running)
uv run pytest tests/integration/ -v
```

## Tech Stack

- **Framework**: FastMCP, Python 3.14
- **Vector Store**: Qdrant
- **Object Storage**: MinIO (S3-compatible)
- **Embeddings**: llama-index + HuggingFace (`intfloat/multilingual-e5-small`)
- **Reranker**: BAAI/bge-reranker-v2-m3
- **Dev Tooling**: uv, Nix, pytest, Docker

## Ports

- Qdrant: 6333 (HTTP), 6334 (gRPC)
- MinIO: 9000 (API), 9001 (Console)
- MCP Server: 8000
- Nginx: 80
