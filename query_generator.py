"""
CYPHER QUERY GENERATOR - FULLY CORRECTED
Uses Llama 3.1:8b with intelligent fallback to template queries
Ensures queries are always generated even if LLM times out
FIXES APPLIED: Schema path, credentials compatibility
"""

import requests
import json
import re
import logging
from typing import Dict, List, Tuple, Optional
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CypherQueryGenerator:
    """
    Generates Cypher queries using Llama 3.1:8b via Ollama
    FIXED: 
    - Correct schema file path
    - Credentials compatible with working setup
    - Template fallback for reliability
    - Proper error handling
    """

    def __init__(self, 
                 model_name: str = "llama3.1:8b",  # ✅ Default to Llama (more reliable)
                 ollama_host: str = "http://localhost:11434",
                 schema_file: str = "Web Page/Road Seafty GPT/neo4j_schema.txt",  # ✅ FIXED: Correct path
                 temperature: float = 0.1,
                 max_tokens: int = 256,  # Reduced for faster response
                 timeout: int = 15):     # Reduced timeout
        """Initialize with faster defaults and correct paths"""
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.schema_file = schema_file
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.api_endpoint = f"{ollama_host}/api/generate"
        self.active_model = None
        self.schema = None

        logger.info(f"🚀 Initializing CypherQueryGenerator")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Schema: {schema_file}")

        self._verify_connection()
        if schema_file:
            self._load_schema()

    def _verify_connection(self):
        """Verify Ollama connection"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=10)
            response.raise_for_status()
            models_data = response.json()
            models = models_data.get("models", [])
            model_names = [m.get('name', '').split(':')[0] for m in models]

            logger.info(f"✓ Ollama connected")
            logger.info(f"✓ Available models: {model_names}")

            model_base = self.model_name.split(':')[0]
            model_exists = any(model_base in name for name in model_names)

            if model_exists:
                self.active_model = self.model_name
                logger.info(f"✓ Using model: {self.model_name}")
            else:
                if any('llama' in name for name in model_names):
                    self.active_model = "llama3.1:8b"
                    logger.warning(f"⚠ Model not found, using: llama3.1:8b")
                else:
                    raise Exception("No suitable model available")

        except Exception as e:
            logger.error(f"✗ Ollama connection failed: {e}")
            raise

    def _load_schema(self):
        """Load schema from file"""
        try:
            # Check if file exists
            if not os.path.exists(self.schema_file):
                logger.warning(f"⚠ Schema file not found: {self.schema_file}")
                logger.info("  Using default schema instead")
                self.schema = self._get_default_schema()
                return

            with open(self.schema_file, 'r') as f:
                self.schema = f.read()
            logger.info(f"✓ Schema loaded from {self.schema_file}")
        except Exception as e:
            logger.warning(f"⚠ Could not load schema: {e}")
            logger.info("  Using default schema")
            self.schema = self._get_default_schema()

    def _get_default_schema(self) -> str:
        """Default schema"""
        return """Road Safety Infrastructure Schema:

Node Labels:
- InfrastructureIssue (s_no, problem, category, type, data, code, clause)

Properties:
- type: 'STOP Sign', 'Speed Bump', 'Hospital Sign'
- problem: 'Damaged', 'Faded', 'Missing', 'Height Issue'
- category: 'Road Sign', 'Road Marking', 'Traffic Calming Measures'
- code: 'IRC:67-2022', 'IRC:35-2015'

Example Queries:
MATCH (i:InfrastructureIssue) WHERE i.type = 'STOP Sign' RETURN i.s_no, i.type, i.problem
MATCH (i:InfrastructureIssue) WHERE i.problem = 'Damaged' RETURN i.type, i.code
MATCH (i:InfrastructureIssue) WHERE i.code = 'IRC:67-2022' RETURN i.type, i.problem"""

    def _build_system_prompt(self) -> str:
        """Build system prompt with schema"""
        schema = self.schema if self.schema else self._get_default_schema()

        return f"""You are a Neo4j Cypher query generator.
Convert natural language to Cypher queries ONLY.
Output ONLY the Cypher query, no explanations.

{schema}

RULES:
1. Always start with MATCH
2. Use WHERE for filtering
3. Always end with RETURN
4. Use case-sensitive values
5. NO markdown, NO explanations, ONLY Cypher"""

    def _get_template_query(self, question: str) -> Optional[str]:
        """
        Generate template query based on keywords
        FALLBACK when LLM times out
        """
        question_lower = question.lower()

        # STOP sign queries
        if 'stop sign' in question_lower or ('stop' in question_lower and 'sign' in question_lower):
            if any(x in question_lower for x in ['regulation', 'govern', 'irc', 'code']):
                return "MATCH (i:InfrastructureIssue) WHERE i.type = 'STOP Sign' RETURN i.s_no, i.type, i.code, i.clause LIMIT 10"
            else:
                return "MATCH (i:InfrastructureIssue) WHERE i.type = 'STOP Sign' RETURN i.s_no, i.type, i.problem, i.category LIMIT 10"

        # Damaged queries
        if 'damaged' in question_lower:
            if 'road sign' in question_lower or 'sign' in question_lower:
                return "MATCH (i:InfrastructureIssue) WHERE i.problem = 'Damaged' AND i.category = 'Road Sign' RETURN i.type, i.problem, i.code LIMIT 10"
            else:
                return "MATCH (i:InfrastructureIssue) WHERE i.problem = 'Damaged' RETURN i.type, i.problem, i.category LIMIT 10"

        # Regulation/IRC queries
        if 'regulation' in question_lower or 'irc' in question_lower:
            if 'irc:67' in question_lower or 'irc 67' in question_lower:
                return "MATCH (i:InfrastructureIssue) WHERE i.code = 'IRC:67-2022' RETURN i.type, i.problem, i.clause LIMIT 10"
            elif 'irc:35' in question_lower or 'irc 35' in question_lower:
                return "MATCH (i:InfrastructureIssue) WHERE i.code = 'IRC:35-2015' RETURN i.type, i.problem, i.clause LIMIT 10"
            else:
                return "MATCH (i:InfrastructureIssue) RETURN DISTINCT i.code, count(i) AS count ORDER BY count DESC LIMIT 10"

        # Road sign category queries
        if 'road sign' in question_lower or ('sign' in question_lower and 'road' in question_lower):
            return "MATCH (i:InfrastructureIssue) WHERE i.category = 'Road Sign' RETURN i.type, i.problem, i.code LIMIT 10"

        # Road marking queries
        if 'road marking' in question_lower or 'marking' in question_lower:
            return "MATCH (i:InfrastructureIssue) WHERE i.category = 'Road Marking' RETURN i.type, i.problem, i.code LIMIT 10"

        # Count/statistics queries
        if any(x in question_lower for x in ['count', 'how many', 'total', 'statistics']):
            return "MATCH (i:InfrastructureIssue) RETURN i.problem, count(i) AS count ORDER BY count DESC LIMIT 10"

        # Speed bump queries
        if 'speed bump' in question_lower:
            return "MATCH (i:InfrastructureIssue) WHERE i.type = 'Speed Bump' RETURN i.s_no, i.type, i.problem, i.category LIMIT 10"

        # Default fallback - get all
        return "MATCH (i:InfrastructureIssue) RETURN i.type, i.problem, i.category, i.code LIMIT 10"

    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama with timeout"""
        system_prompt = self._build_system_prompt()
        full_prompt = f"{system_prompt}\n\nQuestion: {prompt}\n\nCypher Query:"

        try:
            logger.info(f"Querying {self.active_model} (timeout: {self.timeout}s)...")

            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.active_model,
                    "prompt": full_prompt,
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "num_predict": self.max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.Timeout:
            logger.warning(f"⚠ LLM timeout after {self.timeout}s")
            logger.info("  Falling back to template query...")
            return ""  # Will trigger template fallback
        except Exception as e:
            logger.error(f"✗ Ollama error: {e}")
            return ""

    def _clean_query(self, query: str) -> str:
        """Clean and format generated query"""
        if not query:
            return ""

        # Remove markdown code blocks
        if "```" in query:
            parts = query.split("```")
            if len(parts) >= 2:
                query = parts[1]
                if query.startswith("cypher"):
                    query = query[6:]

        # Remove explanatory text
        query = re.sub(r"(?i)^(query:|cypher:|the query|here|answer:).*?\n", "", query)

        # Clean whitespace
        query = "\n".join([line.strip() for line in query.split("\n") if line.strip()])

        return query.strip()

    def _validate_query(self, query: str) -> Tuple[bool, List[str]]:
        """Validate Cypher query structure"""
        errors = []

        if not query:
            errors.append("Empty query generated")
            return False, errors

        # Check for required keywords
        query_upper = query.upper()
        if "MATCH" not in query_upper:
            errors.append("Missing MATCH keyword")
        if "RETURN" not in query_upper:
            errors.append("Missing RETURN keyword")

        # Check balanced parentheses
        if query.count("(") != query.count(")"):
            errors.append("Unbalanced parentheses")

        # Check balanced braces
        if query.count("{") != query.count("}"):
            errors.append("Unbalanced braces")

        is_valid = len(errors) == 0
        return is_valid, errors

    def generate_query(self, natural_language_query: str) -> Dict:
        """
        Generate Cypher query with intelligent fallback

        Args:
            natural_language_query: User's question

        Returns:
            Dict with query result details
        """
        logger.info(f"\nGenerating query for: {natural_language_query[:50]}...")

        start_time = time.time()

        # Try LLM first
        raw_response = self._query_ollama(natural_language_query)
        cleaned_query = self._clean_query(raw_response)

        # If LLM fails/times out, use template
        if not cleaned_query:
            logger.info("✓ Using template query (LLM fallback)")
            cleaned_query = self._get_template_query(natural_language_query)

        generation_time = time.time() - start_time

        # Validate
        is_valid, errors = self._validate_query(cleaned_query)

        result = {
            "success": is_valid and bool(cleaned_query),
            "cypher_query": cleaned_query,
            "is_valid": is_valid,
            "validation_errors": errors,
            "generation_time_seconds": generation_time,
            "model": self.active_model,
            "used_template": not raw_response  # Flag if template was used
        }

        logger.info(f"Generated: {cleaned_query[:80] if cleaned_query else 'NONE'}")
        logger.info(f"Valid: {is_valid}, Time: {generation_time:.1f}s")

        if result["used_template"]:
            logger.info("ℹ Template query used (LLM timeout or fallback)")

        return result


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 TESTING CYPHER GENERATOR - Template Fallback")
    print("="*70 + "\n")

    try:
        gen = CypherQueryGenerator(
            model_name="llama3.1:8b",  # ✅ More reliable than qwen
            timeout=15  # 15 seconds
        )
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        exit(1)

    test_queries = [
        "What regulations govern STOP signs?",
        "Find all damaged road signs",
        "How many issues are there?",
        "Show IRC:67-2022 regulations",
        "Speed bump information",
        "Get all road marking issues"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] Question: {query}")
        print("-" * 70)

        result = gen.generate_query(query)

        if result["success"]:
            print(f"✓ Valid query generated ({result['generation_time_seconds']:.1f}s)")
            print(f"  Cypher: {result['cypher_query']}")
            if result["used_template"]:
                print(f"  ℹ (Using template fallback)")
        else:
            print(f"✗ Generation failed: {result['validation_errors']}")

    print(f"\n{'='*70}")
    print("✓ Testing complete!")
    print("="*70 + "\n")
