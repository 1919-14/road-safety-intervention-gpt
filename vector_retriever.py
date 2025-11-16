"""
VECTOR RETRIEVER - Load from Saved JSON Files (FIXED)
Loads pre-saved chunks.json, embeddings.json, metadata.json
Skips chunking & embedding - uses existing saved data
FIXED: Handles dict embeddings like [{'embedding': [floats]}, ...]
"""

import json
import os
import logging
from typing import List, Dict, Optional
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorRetrieverFromJSON:
    """
    Load and use pre-saved vector data from JSON files
    FIXED: Auto-extracts embeddings from dicts
    Uses: chunks.json, embeddings.json, metadata.json
    """

    def __init__(self, 
                 chunks_file: str = "Web Page/Road Seafty GPT/processed/road_safety_chunks.json",
                 embeddings_file: str = "Web Page/Road Seafty GPT/embeddings/road_safety_embeddings.json",
                 metadata_file: str = "Web Page/Road Seafty GPT/vector_metadata.json"):
        """
        Initialize retriever from JSON files

        Args:
            chunks_file: Path to saved chunks.json
            embeddings_file: Path to saved embeddings.json
            metadata_file: Path to saved metadata.json
        """
        self.chunks_file = chunks_file
        self.embeddings_file = embeddings_file
        self.metadata_file = metadata_file

        self.chunks: List[Dict] = []
        self.embeddings: List[List[float]] = []  # NOW: Guaranteed plain lists
        self.metadata: List[Dict] = []
        self.embedding_model = None

        logger.info("✓ VectorRetrieverFromJSON initialized (FIXED)")
        logger.info(f"  Expected files:")
        logger.info(f"    • {chunks_file}")
        logger.info(f"    • {embeddings_file}")
        logger.info(f"    • {metadata_file}")

    def _extract_embedding_from_item(self, item) -> Optional[List[float]]:
        """
        FIXED: Extract embedding list from dict or return as-is if already list
        Handles structures like:
          - [0.1, -0.2, ...] (plain list)
          - {"embedding": [0.1, -0.2, ...]} (dict with key)
          - {"vector": [0.1, -0.2, ...]} (dict with different key)
        """
        if isinstance(item, list):
            # Already a list - validate it's floats
            try:
                # Spot check first 10 items
                sample = item[:10] if len(item) >= 10 else item
                if all(isinstance(x, (int, float)) for x in sample):
                    return [float(val) for val in item]  # Ensure all floats
                else:
                    logger.warning("Embedding list contains non-numeric values")
                    return None
            except Exception as e:
                logger.warning(f"Error validating list embedding: {e}")
                return None

        elif isinstance(item, dict):
            # Try common embedding keys
            for key in ['embedding', 'vector', 'values', 'features', 'embeddings']:
                if key in item:
                    emb = item[key]
                    if isinstance(emb, list) and len(emb) > 0:
                        try:
                            # Validate floats
                            sample = emb[:10] if len(emb) >= 10 else emb
                            if all(isinstance(x, (int, float)) for x in sample):
                                return [float(val) for val in emb]
                            else:
                                logger.warning(f"Non-numeric values in key '{key}'")
                                continue
                        except Exception as e:
                            logger.warning(f"Error extracting from key '{key}': {e}")
                            continue

            logger.warning(f"No valid embedding found in dict. Keys: {list(item.keys())}")
            return None

        else:
            logger.warning(f"Unexpected embedding item type: {type(item)}")
            return None

    def load_from_json(self) -> bool:
        """
        Load all data from JSON files
        FIXED: Auto-extracts embeddings from dicts or plain lists
        Returns True if successful
        """
        logger.info("\n" + "="*70)
        logger.info("LOADING FROM JSON FILES (FIXED)")
        logger.info("="*70)

        try:
            # Load chunks
            if os.path.exists(self.chunks_file):
                with open(self.chunks_file, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
                logger.info(f"✓ Loaded {len(self.chunks)} chunks from {self.chunks_file}")
            else:
                logger.warning(f"✗ {self.chunks_file} not found")
                return False

            # Load embeddings (FIXED: Auto-extract)
            if os.path.exists(self.embeddings_file):
                with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)

                logger.info(f"Raw embeddings type: {type(raw_data)}")

                # Handle top-level dict like {'embeddings': [...]}
                if isinstance(raw_data, dict) and 'embeddings' in raw_data:
                    raw_embeddings = raw_data['embeddings']
                    logger.info(f"✓ Extracted 'embeddings' key from top-level dict")
                else:
                    raw_embeddings = raw_data

                logger.info(f"Embedding items type: {type(raw_embeddings[0]) if raw_embeddings else 'empty'}")

                # Extract vectors from raw_embeddings (FIXED)
                self.embeddings = []
                for i, item in enumerate(raw_embeddings):
                    emb = self._extract_embedding_from_item(item)
                    if emb is not None:
                        self.embeddings.append(emb)
                    else:
                        logger.warning(f"✗ Invalid embedding at index {i}, skipping...")
                        logger.warning(f"  Item type: {type(item)}, Sample: {str(item)[:100]}")
                        # Don't fail immediately - continue with warning

                if len(self.embeddings) == 0:
                    logger.error("No valid embeddings extracted from file")
                    return False

                logger.info(f"✓ Extracted {len(self.embeddings)} valid embeddings from {self.embeddings_file}")

                # Verify embedding count matches chunks
                if len(self.embeddings) != len(self.chunks):
                    logger.warning(f"⚠ Embedding count ({len(self.embeddings)}) != Chunk count ({len(self.chunks)})")
                    # Try to continue if close
                    if abs(len(self.embeddings) - len(self.chunks)) > 5:
                        return False

                # Get embedding dimension
                emb_dim = len(self.embeddings[0]) if self.embeddings else 0
                logger.info(f"  Embedding dimension: {emb_dim}")
                if emb_dim != 384:
                    logger.warning(f"⚠ Dimension {emb_dim} != expected 384 (check model)")
            else:
                logger.warning(f"✗ {self.embeddings_file} not found")
                return False

            # Load metadata (optional but recommended)
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"✓ Loaded {len(self.metadata)} metadata items from {self.metadata_file}")

                if len(self.metadata) != len(self.chunks):
                    logger.warning(f"⚠ Metadata count ({len(self.metadata)}) != Chunk count ({len(self.chunks)})")
            else:
                logger.warning(f"⚠ {self.metadata_file} not found (optional)")
                # Create default metadata from chunks
                self.metadata = [c.get('metadata', {}) for c in self.chunks]

            logger.info("\n✓ ALL JSON FILES LOADED SUCCESSFULLY (FIXED)")
            logger.info(f"  Total: {len(self.chunks)} chunks with {len(self.embeddings)} embeddings")

            return True

        except Exception as e:
            logger.error(f"✗ Error loading JSON files: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        FIXED: Now guaranteed to receive lists of floats
        """
        try:
            v1 = np.array(vec1, dtype=np.float32)
            v2 = np.array(vec2, dtype=np.float32)

            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)

            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0

            return float(dot_product / (norm_v1 * norm_v2))
        except Exception as e:
            logger.error(f"Error in cosine similarity: {e}")
            return 0.0

    def embed_query(self, query: str) -> Optional[List[float]]:
        """
        Embed query using same model as training
        Returns embedding vector
        """
        try:
            # Try to load sentence transformers for query embedding
            from sentence_transformers import SentenceTransformer

            if self.embedding_model is None:
                logger.info("Loading embedding model for query...")
                self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

            query_embedding = self.embedding_model.encode(query).tolist()
            return query_embedding

        except ImportError:
            logger.error("sentence_transformers not available. Install with: pip install sentence-transformers")
            return None
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            return None

    def retrieve_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Find top-K most similar chunks to query

        Args:
            query: User query string
            top_k: Number of results

        Returns:
            List of similar chunks with similarity scores
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"SEARCHING FOR: '{query}'")
        logger.info(f"Top-K: {top_k}")
        logger.info(f"{'='*70}")

        if not self.chunks or not self.embeddings:
            logger.error("No data loaded. Call load_from_json() first.")
            return []

        # Embed query
        query_embedding = self.embed_query(query)
        if query_embedding is None:
            logger.error("Failed to embed query")
            return []

        # Calculate similarities with all chunks
        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            # FIXED: Both are now guaranteed to be lists of floats
            similarity = self._cosine_similarity(query_embedding, chunk_embedding)
            similarities.append({
                'index': i,
                'chunk_id': self.chunks[i]['chunk_id'],
                'record_id': self.chunks[i]['record_id'],
                'similarity': similarity,
                'chunk_text': self.chunks[i]['chunk_text'],
                'metadata': self.metadata[i] if i < len(self.metadata) else {}
            })

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        # Get top-K
        top_results = similarities[:top_k]

        logger.info(f"✓ Found {len(top_results)} similar chunks")
        for i, r in enumerate(top_results, 1):
            logger.info(f"  {i}. {r['chunk_id']}: {r['similarity']:.2%}")

        return top_results

    def format_retrieval_context(self, results: List[Dict], query: str) -> str:
        """
        Format retrieval results into context for LLM

        Args:
            results: Similar chunks from retrieve_similar()
            query: Original query

        Returns:
            Formatted context string
        """
        if not results:
            return f"""VECTOR RAG CONTEXT
================================================================================
USER QUERY: {query}
RESULTS FOUND: 0
No similar documents found.
================================================================================
"""

        formatted_results = ""
        for idx, result in enumerate(results, 1):
            formatted_results += f"""
RESULT {idx}:
  Chunk ID: {result['chunk_id']}
  Record ID: {result['record_id']}
  Similarity: {result['similarity']:.2%}
  Problem: {result['metadata'].get('problem', 'N/A')}
  Category: {result['metadata'].get('category', 'N/A')}
  Type: {result['metadata'].get('type', 'N/A')}
  Code: {result['metadata'].get('code', 'N/A')}

  Text Preview:
  {result['chunk_text']}...

"""

        context = f"""VECTOR RAG CONTEXT - ROAD SAFETY DATA
================================================================================

USER QUERY: {query}

SEARCH METHOD: Cosine Similarity (Loaded from saved embeddings)

RESULTS FOUND: {len(results)}

{formatted_results}

CONTEXT TYPE: Vector-based semantic search
MODEL: sentence-transformers/all-MiniLM-L6-v2
SOURCE: Pre-saved embeddings from JSON files

================================================================================
"""
        return context

    def retrieve_and_format(self, query: str, top_k: int = 5) -> Optional[str]:
        """
        Complete retrieval: search + format
        Main method to use

        Args:
            query: User query
            top_k: Number of results

        Returns:
            Formatted context for LLM
        """
        # Retrieve
        results = self.retrieve_similar(query, top_k)

        # Format
        context = self.format_retrieval_context(results, query)

        return context

    def get_stats(self) -> Dict:
        """Get retriever statistics"""
        return {
            "chunks_loaded": len(self.chunks),
            "embeddings_loaded": len(self.embeddings),
            "metadata_loaded": len(self.metadata),
            "embedding_dimension": len(self.embeddings[0]) if self.embeddings else 0,
            "chunks_file": self.chunks_file,
            "embeddings_file": self.embeddings_file,
            "metadata_file": self.metadata_file
        }


# Quick usage example
if __name__ == "__main__":
    print("🚀 VECTOR RETRIEVER (FIXED) - LOADING FROM SAVED JSON FILES")
    print()

    # Initialize
    retriever = VectorRetrieverFromJSON(
        chunks_file="Web Page/Road Seafty GPT/processed/road_safety_chunks.json",
        embeddings_file="Web Page/Road Seafty GPT/embeddings/road_safety_embeddings.json",
        metadata_file="Web Page/Road Seafty GPT/vector_metadata.json"
    )

    # Load from JSON
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
        test_queries = [
            
            "How should damaged road signs be reported?"
        ]

        for query in test_queries:
            context = retriever.retrieve_and_format(query, top_k=3)
            print(f"\nQuery: {query}")
            print(context)

    else:
        print("\n✗ Failed to load JSON files")
        print("Make sure the following files exist in the specified paths:")
        print("  1. road-safety-gpt/data/processed/road_safety_chunks.json")
        print("  2. road-safety-gpt/data/embeddings/road_safety_embeddings.json")
        print("  3. road-safety-gpt/data/vector_metadata.json")
        print("\nOr update the file paths in VectorRetrieverFromJSON() call")
