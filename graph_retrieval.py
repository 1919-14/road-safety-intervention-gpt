"""
GRAPH GENERATOR - FIXED
Complete Pipeline: Query Generation → Cypher Query → Neo4j → Extract Data
FIXED: Uses correct CypherQueryGenerator parameters (no 'timeout' as __init__ param)
"""

import logging
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

# Import query generator
from query_generator import CypherQueryGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j Connection Manager"""

    def __init__(self,
                 uri: str = "neo4j://localhost:7687",
                 username: str = "neo4j",
                 password: str = "admin123"):
        """Initialize Neo4j connection"""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.is_connected = False

        logger.info(f"🔗 Connecting to Neo4j: {uri}")
        self._connect()

    def _connect(self) -> bool:
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )

            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")

            logger.info("✓ Connected to Neo4j successfully")
            self.is_connected = True
            return True

        except Exception as e:
            logger.error(f"✗ Connection failed: {e}")
            self.is_connected = False
            return False

    def close(self):
        """Close connection"""
        if self.driver:
            self.driver.close()
            logger.info("✓ Neo4j connection closed")


class GraphGenerator:
    """
    Graph Generator - Main Pipeline
    Uses CypherQueryGenerator to create queries
    Then executes on Neo4j to extract data
    """

    def __init__(self,
                 neo4j_connection: Neo4jConnection,
                 query_generator: CypherQueryGenerator = None):
        """
        Initialize Graph Generator

        Args:
            neo4j_connection: Neo4j connection instance
            query_generator: CypherQueryGenerator instance (optional)
        """
        self.conn = neo4j_connection

        # Initialize query generator if not provided
        if query_generator is None:
            try:
                # ✅ FIXED: Use correct parameters (no 'timeout' as __init__ param)
                self.query_gen = CypherQueryGenerator(
                    model_name="llama3.1:8b",
                    ollama_host="http://localhost:11434",
                    schema_file="neo4j_schema.txt"
                    # ✅ 'timeout' is not a __init__ parameter, it's used internally
                )
                logger.info("✓ Query generator initialized")
            except Exception as e:
                logger.error(f"⚠ Query generator failed: {e}")
                self.query_gen = None
        else:
            self.query_gen = query_generator

        if not self.conn.is_connected:
            raise Exception("Neo4j not connected")

        logger.info("✓ GraphGenerator initialized")

    def generate_and_execute(self, natural_language_query: str) -> Dict:
        """
        Generate Cypher query and execute on Neo4j

        Args:
            natural_language_query: User's natural language question

        Returns:
            Dict with results and metadata
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"GRAPH GENERATION & EXTRACTION")
        logger.info(f"{'='*70}")
        logger.info(f"User Query: {natural_language_query}")

        result = {
            "success": False,
            "query": natural_language_query,
            "cypher": None,
            "records": [],
            "count": 0,
            "error": None
        }

        # Step 1: Generate Cypher query
        if not self.query_gen:
            result["error"] = "Query generator not available"
            logger.error(result["error"])
            return result

        logger.info("\n[1/3] Generating Cypher query...")
        gen_result = self.query_gen.generate_query(natural_language_query)

        if not gen_result.get("success") or not gen_result.get("cypher_query"):
            result["error"] = f"Query generation failed: {gen_result.get('validation_errors')}"
            logger.error(result["error"])
            return result

        cypher_query = gen_result["cypher_query"]
        result["cypher"] = cypher_query
        logger.info(f"✓ Generated Cypher:")
        logger.info(f"  {cypher_query}")

        # Step 2: Execute Cypher on Neo4j
        logger.info("\n[2/3] Executing query on Neo4j...")
        try:
            with self.conn.driver.session() as session:
                exec_result = session.run(cypher_query)
                records = exec_result.data()

            result["records"] = records
            result["count"] = len(records)
            logger.info(f"✓ Retrieved {len(records)} records")

        except Exception as e:
            result["error"] = f"Query execution failed: {e}"
            logger.error(result["error"])
            return result

        # Step 3: Format results
        logger.info("\n[3/3] Formatting results...")
        result["success"] = True
        logger.info(f"✓ Complete! {len(records)} records retrieved")

        return result

    def format_results(self, result: Dict) -> str:
        """Format results for display"""
        if not result["success"]:
            return f"\n❌ Error: {result['error']}\n"

        formatted = f"""
{'='*70}
✓ GRAPH GENERATION & EXTRACTION RESULTS
{'='*70}

User Query:
  {result['query']}

Generated Cypher:
  {result['cypher']}

Results: {result['count']} records
{'='*70}

"""

        # Format records
        for i, record in enumerate(result["records"][:10], 1):
            formatted += f"\n[{i}] "
            for key, value in record.items():
                if isinstance(value, str) and len(str(value)) > 80:
                    value = str(value)[:80] + "..."
                formatted += f"{key}: {value}, "
            formatted = formatted.rstrip(", ") + "\n"

        if result["count"] > 10:
            formatted += f"\n... and {result['count'] - 10} more records\n"

        formatted += f"{'='*70}\n"
        return formatted

    def close(self):
        """Close connections"""
        if self.conn:
            self.conn.close()


class GraphPipeline:
    """Complete pipeline for main_app.py integration"""

    def __init__(self,
                 neo4j_uri: str = "neo4j://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "admin123",
                 ollama_host: str = "http://localhost:11434"):
        """Initialize complete pipeline"""
        logger.info("\n🚀 Initializing Graph Pipeline")

        # Create connections
        self.neo4j_conn = Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password)

        if not self.neo4j_conn.is_connected:
            raise Exception("Neo4j connection failed")

        # Create query generator
        try:
            # ✅ FIXED: Use correct parameters (no 'timeout' as __init__ param)
            self.query_gen = CypherQueryGenerator(
                model_name="llama3.1:8b",
                ollama_host=ollama_host,
                schema_file="neo4j_schema.txt"
                # ✅ No 'timeout' parameter here
            )
        except Exception as e:
            logger.warning(f"⚠ Query generator failed: {e}")
            self.query_gen = None

        # Create graph generator
        self.graph_gen = GraphGenerator(self.neo4j_conn, self.query_gen)

        logger.info("✓ Graph Pipeline Ready")

    def query(self, natural_language_query: str) -> Dict:
        """
        Execute query through complete pipeline

        Args:
            natural_language_query: User's question

        Returns:
            Dict with results
        """
        return self.graph_gen.generate_and_execute(natural_language_query)

    def query_and_format(self, natural_language_query: str) -> str:
        """Execute query and return formatted results"""
        result = self.query(natural_language_query)
        return self.graph_gen.format_results(result)

    def close(self):
        """Close pipeline"""
        self.graph_gen.close()


def main_usage():
    """Example usage for main_app.py"""

    print("\n🎯 GRAPH GENERATOR - Complete Pipeline\n")

    # Initialize pipeline
    try:
        pipeline = GraphPipeline(
            neo4j_uri="neo4j://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="admin123",
            ollama_host="http://localhost:11434"
        )
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    # Test queries
    test_queries = [
        "How should damaged road signs be reported?"
    ]

    for query in test_queries:
        print(f"\nUser Query: {query}")

        # Get results
        result = pipeline.query(query)

        # Display results
        print(result)

    # Close
    pipeline.close()
    print("✓ Complete\n")


if __name__ == "__main__":
    main_usage()
