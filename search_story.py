import requests
import chromadb


QUESTION = "How can I create a new employee?"

# -----------------------------------------------
# Generate question embedding
# -----------------------------------------------

response = requests.post(
    "http://localhost:11434/api/embed",
    json={
        "model": "qwen3-embedding:0.6b",
        "input": QUESTION
    }
)

response.raise_for_status()

question_embedding = response.json()["embeddings"][0]


# -----------------------------------------------
# Connect to ChromaDB
# -----------------------------------------------

client = chromadb.HttpClient(
    host="localhost",
    port=8000
)

collection = client.get_collection(
    name="azuredevops_stories"
)


# -----------------------------------------------
# Semantic search
# -----------------------------------------------

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=5
)


# -----------------------------------------------
# Display results
# -----------------------------------------------

for i, document in enumerate(results["documents"][0]):

    print("\n-----------------------------")
    print(f"Result #{i + 1}")

    print(
        f"Distance: "
        f"{results['distances'][0][i]}"
    )

    print(document)

    print(
        "Metadata:",
        results["metadatas"][0][i]
    )