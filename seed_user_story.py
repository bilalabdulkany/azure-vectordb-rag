import requests
import chromadb


OLLAMA_URL = "http://localhost:11434"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000


# --------------------------------------------------
# Story from Azure DevOps
# --------------------------------------------------

story_id = 842

title = "Display New Employee Form"

description = (
    "As an user when I click on New button, "
    "I want to see the New Employee Form "
    "so that I can enter details of the new employee."
)

document = f"""
Title: {title}

Description:
{description}
""".strip()


# --------------------------------------------------
# Generate embedding using Ollama
# --------------------------------------------------

response = requests.post(
    f"{OLLAMA_URL}/api/embed",
    json={
        "model": "qwen3-embedding:0.6b",
        "input": document
    }
)

response.raise_for_status()

embedding = response.json()["embeddings"][0]

print(f"Embedding dimensions: {len(embedding)}")


# --------------------------------------------------
# Connect to ChromaDB
# --------------------------------------------------

client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT
)

collection = client.get_or_create_collection(
    name="azuredevops_stories"
)


# --------------------------------------------------
# Store Story
# --------------------------------------------------

collection.upsert(
    ids=[str(story_id)],

    documents=[document],

    embeddings=[embedding],

    metadatas=[{
        "work_item_id": story_id,
        "work_item_type": "User Story",
        "state": "New",
        "area_path": "VectorPOC",
        "iteration_path": "VectorPOC",
        "assigned_to": "Abdel Raoof"
    }]
)


print("Story 842 inserted successfully.")

print(f"Collection count: {collection.count()}")