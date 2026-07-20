import argparse
from config import settings
from services.vector_store import QdrantService
from services.search_engine import RAGSearchEngine


def main():
    parser = argparse.ArgumentParser(description="Запрос к RAG-базе через консоль")
    parser.add_argument("--query", type=str, required=True, help="Текст вашего вопроса")
    parser.add_argument("--top-k", type=int, default=30, help="Количество кандидатов из вектора")
    parser.add_argument("--top-n", type=int, default=5, help="Итоговое количество чанков")
    args = parser.parse_args()

    print("Инициализация сервисов поиска...")
    qdrant_service = QdrantService()
    search_engine = RAGSearchEngine(qdrant_service=qdrant_service)

    print(f"\nВыполнение поиска по запросу: '{args.query}'...")
    result_text = search_engine.search(
        query_text=args.query,
        top_k_candidates=args.top_k,
        top_n_final=args.top_n
    )

    print("\n" + "=" * 60)
    print(" РЕЗУЛЬТАТЫ ПОИСКА:")
    print("=" * 60 + "\n")
    print(result_text)


if __name__ == "__main__":
    main()