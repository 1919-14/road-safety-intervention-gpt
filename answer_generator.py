"""
ANSWER GENERATOR - Generates answers using Llama 3.1:8b local
Uses Ollama for local LLM inference
"""

import logging
import requests
from typing import Optional, Dict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnswerGenerator:
    """
    Generate answers using Llama 3.1:8b running locally via Ollama
    """

    def __init__(self, 
                 model_name: str = "llama3.1:8b",
                 ollama_url: str = "http://localhost:11434"):
        """
        Initialize Answer Generator

        Args:
            model_name: Llama model to use (default: llama3.1:8b)
            ollama_url: URL of local Ollama server
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.generate_endpoint = f"{ollama_url}/api/generate"

        logger.info(f"✓ AnswerGenerator initialized")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Ollama URL: {ollama_url}")

        # Check connection
        self._check_ollama_connection()

    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Connected to Ollama server")
                models = response.json().get('models', [])
                model_names = [m.get('name', '').split(':')[0] for m in models]
                logger.info(f"  Available models: {model_names}")

                # Check if llama3.1 is available
                if any('llama' in m.lower() for m in model_names):
                    logger.info(f"  ✓ {self.model_name} is available")
                else:
                    logger.warning(f"⚠ {self.model_name} might not be available")
                    logger.warning("  To install: ollama pull llama3.1:8b")

                return True
            else:
                logger.error(f"✗ Ollama returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Cannot connect to Ollama at {self.ollama_url}")
            logger.error("  Make sure Ollama is running: ollama serve")
            return False
        except Exception as e:
            logger.error(f"✗ Error checking Ollama: {e}")
            return False

    def generate(self,
                graph_context: str,
                vector_context: str,
                query: str,
                temperature: float = 0.7,
                max_tokens: int = 500,
                stream: bool = False) -> Optional[str]:
        """
        Generate answer using Llama 3.1:8b

        Args:
            context: Merged RAG context
            query: User question
            temperature: Model temperature (0.0-1.0)
            max_tokens: Maximum response length
            stream: Whether to stream response

        Returns:
            Generated answer text
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"GENERATING ANSWER WITH LLAMA 3.1:8B")
        logger.info(f"{'='*70}")
        logger.info(f"Query: {query}")
        logger.info(f"Context length: {len(graph_context)} chars")
        logger.info(f"Context length: {len(vector_context)} chars")

        # Build prompt
        prompt = f"""You are a Road Safety Expert Assistant. Use ONLY the information provided in the context. 
Do NOT add external knowledge. If any information is missing, clearly state it.

QUESTION:
{query}

NEO4J CONTEXT:
{graph_context}

VECTOR CONTEXT:
{vector_context}

RESPONSE RULES:
1. Answer must be clear, explainable, and strictly based on context.
2. Use **bold headings** exactly as shown below.
3. Use *bullet points* for lists.
4. Cite IRC standards, codes, and clauses exactly as present in context.
5. Provide only context-supported interventions and recommendations.
6. If information is missing, write: *"Insufficient information in the provided context."*

You are a Road Safety Expert Assistant working under strict RAG rules.

Your job: Provide a clean, professional answer using ONLY the context, with bold headings and bullet points.

If any part cannot be answered, explicitly state that due to missing context.

don't use any information from outer source to answer or in answer all information from context

OUTPUT FORMAT (STRICT):

**Direct and Professional Answer:**
- straight answer without any relations explanation

**Reference to IRC Standards:**
- *List standards and clauses mentioned in context.*

if available
**Interventions with Specifications:**
- *Intervention 1 (with clause)*  
- *Intervention 2 (with clause)*

**Standard Codes and Clause Numbers:**
- *IRC code + clause list*
if available
**Actionable Recommendations:**
- *Recommendation 1*  
- *Recommendation 2*

FINAL RESPONSE:


"""

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": stream
        }

        try:
            logger.info(f"Sending request to Ollama ({self.model_name})...")
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                if stream:
                    # Streaming response
                    full_response = ""
                    logger.info("✓ Streaming response:")

                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            chunk = data.get('response', '')
                            full_response += chunk
                            print(chunk, end='', flush=True)

                    print()  # New line after streaming
                    logger.info(f"\n✓ Response complete ({len(full_response)} chars)")
                    return full_response
                else:
                    # Full response
                    response_data = response.json()
                    answer = response_data.get('response', '')

                    logger.info(f"✓ Response received ({len(answer)} chars)")
                    return answer
            else:
                logger.error(f"✗ Ollama returned status {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error("✗ Request timeout - Llama 3.1 taking too long")
            logger.error("  Try reducing max_tokens or check system resources")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Cannot connect to Ollama at {self.ollama_url}")
            logger.error("  Make sure Ollama is running: ollama serve")
            return None
        except Exception as e:
            logger.error(f"✗ Error generating answer: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_with_context(self,
                             merged_context_dict: Dict,
                             temperature: float = 0.1,
                             max_tokens: int = 500) -> Optional[str]:
        """
        Generate answer explained from merged context dict and also give reference of answering

        Args:
            merged_context_dict: Dict from ContextMerger.merge_contexts()

        Returns:
            Generated answer
        """
        return self.generate(
            context=merged_context_dict["merged_context"],
            query=merged_context_dict["query"],
            temperature=temperature,
            max_tokens=max_tokens
        )


if __name__ == "__main__":
    # Test
    print("🚀 ANSWER GENERATOR - Testing Llama 3.1:8b")
    print()

    generator = AnswerGenerator()

    # Test context
    vector_context = """

RESULT 1:
  Chunk ID: chunk_6
  Record ID: 6
  Similarity: 58.68%
  Problem: N/A
  Category: N/A
  Type: N/A
  Code: N/A

  Text Preview:
  Record ID: 6
Problem: Obstruction
Category: Road Sign
Type: Crash Prone Area Ahead Sign
Code: IRC:67-2022
Clause: 11.2
Description: Drivers and other road users must have a clear and unobstructed view of road signs to ensure safe navigation. The area that shall remain free from obstructions to the sight line, whether caused by vegetation (e.g., bushes, trees), other signs, or street furniture (e.g., crash barriers), is referred to as the clear visibility distance. This distance shall increase as traffic speeds rise to provide sufficient reaction time. Road signs or their supports (including front and back) shall not display any form of advertisement or message unrelated to traffic control (as per clause 2.3)....


RESULT 2:
  Chunk ID: chunk_10
  Record ID: 10
  Similarity: 53.78%
  Problem: N/A
  Category: N/A
  Type: N/A
  Code: N/A

  Text Preview:
  Record ID: 10
Problem: Obstruction
Category: Road Sign
Type: Bus Stop Sign
Code: IRC:67-2022
Clause: 11.2
Description: Drivers and other road users must have a clear and unobstructed view of road signs to ensure safe navigation. The area that should remain free from obstructions to the sight line, whether caused by vegetation (e.g., bushes, trees), other signs, or street furniture (e.g., crash barriers), is referred to as the clear visibility distance. This distance should increase as traffic speeds rise to provide sufficient reaction time.
Road signs or their supports (including front and back) shall not display any form of advertisement or message unrelated to traffic control (as per clause 2.3)....


RESULT 3:
  Chunk ID: chunk_17
  Record ID: 17
  Similarity: 53.03%
  Problem: N/A
  Category: N/A
  Type: N/A
  Code: N/A

  Text Preview:
  Record ID: 17
Problem: Wrongly Placed
Category: Road Sign
Type: Pedestrian Crossing Informatory Signs
Code: IRC:67-2022
Clause: 2.3
Description: Road signs shall be placed and operated in a consistent manner, positioned appropriately with respect to the location or situation to which they apply. Signs that are not necessary or no longer required shall be removed....

"""
    graph_context ="""
    {'success': True, 'query': 'How should damaged road signs be reported?', 'cypher': "MATCH (i:InfrastructureIssue) 
    WHERE i.category = 'Road Sign' AND i.problem = 'Damaged' RETURN i.s_no, i.type, i.code", 'records': [{'i.s_no': 1, 'i.type': 'STOP Sign', 'i.code': 'IRC:67-2022'}, {'i.s_no': 11, 'i.type': 'Truck Lay-By Sign', 'i.code': 'IRC:67-2022'}, 
    {'i.s_no': 14, 'i.type': 'Axle Load Limit Sign', 'i.code': 'IRC:67-2022'}], 'count': 3, 'error': None}
    """
    test_query = "How should damaged road signs be reported?"

    answer = generator.generate(vector_context, graph_context, test_query, max_tokens=200)

    if answer:
        print("\n✓ Generated answer:")
        print(answer)
    else:
        print("\n✗ Failed to generate answer")
        print("Make sure Ollama is running with llama3.1:8b model")
