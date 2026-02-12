import logging
import time
from typing import Any

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from app.config.config import get_settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manager for MongoDB Atlas interactions with vector search support."""

    def __init__(self) -> None:
        """Initialize MongoDB client."""
        self.settings = get_settings()
        self._client: MongoClient | None = None
        self._db = None
        self._collection = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to MongoDB Atlas."""
        try:
            self._client = MongoClient(
                self.settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
            )
            # Verify connectivity
            self._client.admin.command("ping")

            self._db = self._client[self.settings.mongodb_database]
            self._collection = self._db[self.settings.mongodb_collection]

            logger.info(
                f"Connected to MongoDB Atlas - "
                f"Database: {self.settings.mongodb_database}, "
                f"Collection: {self.settings.mongodb_collection}"
            )
        except ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB Atlas: {e}")
            self._client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self._client = None

    def close(self) -> None:
        """Close the MongoDB client."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")

    def vector_search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """
        Perform vector similarity search using MongoDB Atlas Vector Search.

        Args:
            query_embedding: The query embedding vector (768 dimensions for Gemini).
            top_k: Number of top results to return.

        Returns:
            List of matching documents with scores.
        """
        if not self._client or not self._collection:
            self._connect()
            if not self._client:
                logger.warning("MongoDB client is not available. Skipping search.")
                return []

        try:
            start_time = time.time()

            # MongoDB Atlas Vector Search aggregation pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",  # Must be created in Atlas UI
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": top_k * 10,  # Oversample for better results
                        "limit": top_k,
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "id": 1,
                        "title": 1,
                        "content": 1,
                        "category": 1,
                        "tags": 1,
                        "language": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]

            results = list(self._collection.aggregate(pipeline))

            duration = (time.time() - start_time) * 1000
            logger.debug(
                f"MongoDB vector search completed in {duration:.2f}ms, found {len(results)} results"
            )

            return results

        except OperationFailure as e:
            logger.error(
                f"MongoDB vector search failed: {e}. "
                "Make sure you have created a vector search index named 'vector_index' "
                "in MongoDB Atlas."
            )
            return []
        except Exception as e:
            logger.error(f"Error executing MongoDB vector search: {e}")
            return []

    def insert_documents(self, documents: list[dict[str, Any]]) -> int:
        """
        Insert multiple documents into the collection.

        Args:
            documents: List of documents to insert.

        Returns:
            Number of documents inserted.
        """
        if not self._client or not self._collection:
            self._connect()
            if not self._client:
                logger.warning("MongoDB client is not available. Skipping insert.")
                return 0

        try:
            result = self._collection.insert_many(documents)
            count = len(result.inserted_ids)
            logger.info(f"Inserted {count} documents into MongoDB")
            return count
        except Exception as e:
            logger.error(f"Error inserting documents: {e}")
            return 0

    def count_documents(self, filter_query: dict[str, Any] | None = None) -> int:
        """
        Count documents in the collection.

        Args:
            filter_query: Optional filter query.

        Returns:
            Number of documents.
        """
        if not self._client or not self._collection:
            self._connect()
            if not self._client:
                return 0

        try:
            return self._collection.count_documents(filter_query or {})
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0

    def delete_all_documents(self) -> int:
        """
        Delete all documents from the collection (use with caution).

        Returns:
            Number of documents deleted.
        """
        if not self._client or not self._collection:
            self._connect()
            if not self._client:
                return 0

        try:
            result = self._collection.delete_many({})
            logger.info(f"Deleted {result.deleted_count} documents from MongoDB")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return 0


# Global instance
_mongodb_manager = None


def get_mongodb_manager() -> MongoDBManager:
    """Get or create the global MongoDB manager instance."""
    global _mongodb_manager
    if _mongodb_manager is None:
        _mongodb_manager = MongoDBManager()
    return _mongodb_manager
