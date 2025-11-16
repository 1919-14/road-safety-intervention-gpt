# backend-server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from graph_retrieval import GraphPipeline
from vector_retriever import VectorRetrieverFromJSON
from answer_generator import AnswerGenerator
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Initialize components
try:
    pipeline = GraphPipeline(
        neo4j_uri="neo4j://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="admin123",
        ollama_host="http://localhost:11434"
    )
    logger.info("GraphPipeline initialized successfully")
except Exception as e:
    logger.error(f"Error initializing GraphPipeline: {e}")
    pipeline = None

try:
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

    else:
        print("\n✗ Failed to load JSON files")
        print("Make sure the following files exist in the specified paths:")
        print("  1. road_safety_chunks.json")
        print("  2. road_safety_embeddings.json")
        print("  3. vector_metadata.json")
        print("\nOr update the file paths in VectorRetrieverFromJSON() call")
    logger.info("VectorRetriever initialized successfully")
except Exception as e:
    logger.error(f"Error initializing VectorRetriever: {e}")
    retriever = None

generator = AnswerGenerator()


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint that processes user queries through the RAG pipeline
    """
    try:
        data = request.get_json()
        query = data.get('message', '').strip()
        
        if not query:
            return jsonify({'error': 'Empty query'}), 400
        
        logger.info(f"Processing query: {query}")
        
        # Get results from graph pipeline
        graph_result = None
        if pipeline:
            try:
                graph_result = pipeline.query(query)
                logger.info(f"Graph result: {graph_result}")
            except Exception as e:
                logger.error(f"Error in graph query: {e}")
                graph_result = None
        
        # Get results from vector retriever
        vector_result = None
        if retriever:
            try:
                vector_result = retriever.retrieve_and_format(query, top_k=3)
                print(vector_result)
                logger.info(f"Vector result: {vector_result}")
            except Exception as e:
                logger.error(f"Error in vector retrieval: {e}")
                vector_result = None
        
        # Generate final answer
        try:
            answer = generator.generate(graph_result, vector_result, query, max_tokens=500)
            logger.info(f"Generated answer: {answer}")
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            answer = "I encountered an error while processing your query. Please try again."
        
        return jsonify({
            'response': answer,
            'graph_result': str(graph_result) if graph_result else None,
            'vector_result': str(vector_result) if vector_result else None,
            'query': query
        }), 200
    
    except Exception as e:
        logger.error(f"Unexpected error in /api/chat: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    status = {
        'status': 'healthy',
        'pipeline': 'ready' if pipeline else 'not initialized',
        'retriever': 'ready' if retriever else 'not initialized',
        'generator': 'ready'
    }
    return jsonify(status), 200


@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    """
    Placeholder for chat history retrieval
    """
    return jsonify({
        'history': [
            {
                'title': 'Speed Limit Query',
                'date': 'Today',
                'messages': []
            }
        ]
    }), 200


if __name__ == '__main__':
    logger.info("Starting Road Safety GPT Backend Server...")
    app.run(debug=True, host='0.0.0.0', port=5000)