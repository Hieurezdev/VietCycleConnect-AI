import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Try to load .env manually if dotenv is missing
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("Loaded .env using python-dotenv")
except ImportError:
    print("python-dotenv not found, loading .env manually")
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        os.environ[key] = value.strip('"').strip("'")
                    except ValueError:
                        continue
        print(f"Loaded .env manually from {env_path}")
    else:
        print(f"No .env file found at {env_path}")

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.infra.mongodb import get_mongodb_manager
from app.services.embedding_service import get_embedding_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent / "data" / "knowledge_base_sample.json"


def ingest_data():
    """Ingest sample data into MongoDB with embeddings."""
    if not DATA_FILE.exists():
        logger.error(f"Data file not found: {DATA_FILE}")
        return

    logger.info(f"Reading data from {DATA_FILE}")
    with open(DATA_FILE, encoding="utf-8") as f:
        documents = json.load(f)

    mongo_manager = get_mongodb_manager()
    embedding_service = get_embedding_service()

    # Check connection
    try:
        mongo_manager.count_documents()
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return

    logger.info(f"Found {len(documents)} documents to ingest")

    documents_to_insert = []

    for doc in documents:
        try:
            # Combine title and content for embedding
            text_to_embed = f"{doc['title']}\n{doc['content']}"

            # Generate embedding
            logger.info(f"Generating embedding for: {doc['title']}")
            embedding = embedding_service.embed_query(text_to_embed)

            # Add metadata
            new_doc = doc.copy()
            new_doc["embedding"] = embedding
            new_doc["created_at"] = datetime.utcnow()
            new_doc["updated_at"] = datetime.utcnow()

            documents_to_insert.append(new_doc)

        except Exception as e:
            logger.error(f"Error processing document {doc['id']}: {e}")

    if documents_to_insert:
        # Optional: Clear existing data
        # mongo_manager.delete_all_documents()

        count = mongo_manager.insert_documents(documents_to_insert)
        logger.info(f"Successfully inserted {count} documents into MongoDB")
    else:
        logger.warning("No documents prepared for insertion")

    print("\n" + "=" * 50)
    print("IMPORTANT: NEXT STEPS FOR ATLAS VECTOR SEARCH")
    print("=" * 50)
    print("1. Go to MongoDB Atlas UI > Database > Atlas Search")
    print("2. Create a Search Index")
    print("3. Choose 'JSON Editor'")
    print("4. Select database: 'vietcycle_knowledge', collection: 'knowledge_base'")
    print("5. Name the index: 'vector_index'")
    print("6. Paste the following configuration:")
    print("""
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 768,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "category"
    }
  ]
}
    """)
    print("=" * 50 + "\n")


if __name__ == "__main__":
    ingest_data()
