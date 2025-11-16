from graph_retrieval import GraphPipeline
from vector_retriever import VectorRetrieverFromJSON
from answer_generator import AnswerGenerator

pipeline = GraphPipeline(
            neo4j_uri="neo4j://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="admin123",
            ollama_host="http://localhost:11434"
            )

query = "What does the STOP sign indicate according to IRC:67-2022, Clause 14.4?"

graph_result = pipeline.query(query)

generator = AnswerGenerator()

retriever = VectorRetrieverFromJSON(
        chunks_file="Web Page/Road Seafty GPT/processed/road_safety_chunks.json",
        embeddings_file="Web Page/Road Seafty GPT/embeddings/road_safety_embeddings.json",
        metadata_file="Web Page/Road Seafty GPT/vector_metadata.json"
    )

if retriever.load_from_json():
        print("\n✓ Successfully loaded all JSON files!")

        # Show stats
        stats = retriever.get_stats()
        print(f"\nStats:")
        print(f"  Chunks: {stats['chunks_loaded']}")
        print(f"  Embeddings: {stats['embeddings_loaded']}")
        print(f"  Embedding dim: {stats['embedding_dimension']}")

        # Test retrieval
        print("\nTesting retrieval...")
        
        vector_result = retriever.retrieve_and_format(query, top_k=3)

else:
    print("\n✗ Failed to load JSON files")
    print("Make sure the following files exist in the specified paths:")
    print("  1. road_safety_chunks.json")
    print("  2. road_safety_embeddings.json")
    print("  3. vector_metadata.json")
    print("\nOr update the file paths in VectorRetrieverFromJSON() call")

answer = generator.generate(graph_result, vector_result, query, max_tokens=500)
print(answer)
# print(vector_result)
# print(graph_result)