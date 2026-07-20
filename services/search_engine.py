import torch
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.vector_stores.qdrant import QdrantVectorStore

from config import settings
from services.vector_store import QdrantService
from utils.text_processing import format_chunk_output


class RAGSearchEngine:
    def __init__(self, qdrant_service: QdrantService):
        self.qdrant_service = qdrant_service
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 1. Модель эмбеддингов
        # Текстовые инструкции для E5 задаются штатным способом через query_instruction и text_instruction
        self.embed_model = HuggingFaceEmbedding(
            model_name=settings.embed_model_name,
            device=self.device,
            query_instruction="query: ",
            text_instruction="passage: "
        )

        # 2. Инициализация VectorStore и Index
        self.vector_store = QdrantVectorStore(
            collection_name=settings.collection_name,
            client=self.qdrant_service.client,
            enable_hybrid=False
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context,
            embed_model=self.embed_model
        )

        # 3. Реранкер
        self.reranker = SentenceTransformerRerank(
            model=settings.reranker_model_name,
            top_n=5,
            device=self.device
        )

    def search(
        self,
        query_text: str,
        top_k_candidates: int = 30,
        top_n_final: int = 5
    ) -> str:
        """Выполняет двухэтапный семантический поиск (Retrieval + Reranking)."""
        retriever = self.index.as_retriever(
            similarity_top_k=top_k_candidates,
            vector_store_query_mode="default"
        )
        raw_nodes = retriever.retrieve(query_text)

        if not raw_nodes:
            return "По вашему запросу ничего не найдено."

        self.reranker.top_n = top_n_final
        final_nodes = self.reranker.postprocess_nodes(raw_nodes, query_str=query_text)

        results = []
        for node_with_score in final_nodes:
            node = node_with_score.node
            formatted = format_chunk_output(
                chunk_text=node.get_content(),
                metadata=node.metadata,
                public_url_base=settings.minio_public_url,
                score=node_with_score.score
            )
            results.append(formatted)

        return "\n\n".join(results)