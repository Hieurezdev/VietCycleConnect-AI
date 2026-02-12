import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import HumanMessage

from app.agents.langgraph_orchestrator import app_graph

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scrap_matching():
    print("\n=== Testing Scrap Matching (ID Only) ===")

    # Mock input for scrap matching
    initial_state = {
        "messages": [HumanMessage(content="Tôi muốn bán sắt vụn")],
        "use_knowledge_base": False,
        "context": "",
        "next_step": "",
        "output": "",
    }

    # Stream the graph execution
    async for output in app_graph.astream(initial_state):
        for node_name, state_update in output.items():
            print(f"\n--- Node: {node_name} ---")
            if "context" in state_update:
                print(f"Context Preview: {state_update['context'][:200]}...")
            if "messages" in state_update:
                print(f"Response: {state_update['messages'][-1].content}")


async def test_knowledge_base():
    print("\n=== Testing Knowledge Base Mode ===")

    # Mock input for knowledge base
    initial_state = {
        "messages": [HumanMessage(content="Làm sao để đăng ký tài khoản?")],
        "use_knowledge_base": True,
        "context": "",
        "next_step": "",
        "output": "",
    }

    # Stream the graph execution
    async for output in app_graph.astream(initial_state):
        for node_name, state_update in output.items():
            print(f"\n--- Node: {node_name} ---")
            if "context" in state_update:
                print(f"Context Preview: {state_update['context'][:200]}...")
            if "messages" in state_update:
                print(f"Response: {state_update['messages'][-1].content}")


async def main():
    await test_scrap_matching()
    await test_knowledge_base()


if __name__ == "__main__":
    asyncio.run(main())
