import logging
import time
from typing import Any

from neo4j import GraphDatabase, Neo4jDriver
from neo4j.exceptions import ServiceUnavailable

from app.config.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jManager:
    """Manager for Neo4j Graph Database interactions."""

    def __init__(self) -> None:
        """Initialize Neo4j driver."""
        self.settings = get_settings()
        self._driver: Neo4jDriver | None = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_username, self.settings.neo4j_password),
            )
            # Verify connectivity
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j Graph Database")
        except ServiceUnavailable as e:
            logger.error(f"Could not connect to Neo4j: {e}")
            self._driver = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            self._driver = None

    def close(self) -> None:
        """Close the Neo4j driver."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")

    def execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query.

        Args:
            query: The Cypher query string.
            parameters: Dictionary of parameters for the query.

        Returns:
            List of records as dictionaries.
        """
        if not self._driver:
            self._connect()
            if not self._driver:
                logger.warning("Neo4j driver is not available. Skipping query.")
                return []

        try:
            start_time = time.time()
            records, summary, keys = self._driver.execute_query(
                query,
                parameters_=parameters,
                database_="neo4j",  # Default database
            )
            # summary uses result_available_after and result_consumed_after which are in ms?
            # Actually just checking time manually is fine.
            duration = (time.time() - start_time) * 1000
            logger.debug(f"Executed Cypher query in {duration:.2f}ms: {query[:50]}...")

            # records is a list of Record objects, convert to dict
            return [record.data() for record in records]

        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            return []

    # Helper method for vector search if using Neo4j Vector Index
    def vector_search(
        self, index_name: str, vector: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Perform a vector similarity search in Neo4j (GraphRAG).

        Assumes a vector index exists on the nodes.
        Uses db.index.vector.queryNodes procedure.
        """
        query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $vector)
        YIELD node, score
        RETURN node, score
        """
        params = {"index_name": index_name, "vector": vector, "top_k": top_k}
        return self.execute_query(query, params)


# Global instance or Dependency Injection provider could be used
_neo4j_manager = None


def get_neo4j_manager() -> Neo4jManager:
    global _neo4j_manager
    if _neo4j_manager is None:
        _neo4j_manager = Neo4jManager()
    return _neo4j_manager
