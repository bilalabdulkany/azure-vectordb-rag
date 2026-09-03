import requests
import chromadb


OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"
LLM_MODEL = "qwen3:4b"

QUESTION = "How can I create a new employee?"


# ============================================================
# 1. Generate embedding for the user's question
# ============================================================

print("Generating question embedding...")

response = requests.post(
    f"{OLLAMA_URL}/api/embed",
    json={
        "model": EMBEDDING_MODEL,
        "input": QUESTION
    }
)

response.raise_for_status()

question_embedding = response.json()["embeddings"][0]


# ============================================================
# 2. Connect to ChromaDB
# ============================================================

print("Searching ChromaDB...")

client = chromadb.HttpClient(
    host="localhost",
    port=8000
)

collection = client.get_collection(
    name="azuredevops_stories"
)


# ============================================================
# 3. Search for relevant stories
# ============================================================

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=5
)


# ============================================================
# 4. Build context for Qwen
# ============================================================

context_parts = []

for i, document in enumerate(results["documents"][0]):

    metadata = results["metadatas"][0][i]

    context_parts.append(
        f"""
--- Requirement {i + 1} ---

Work Item ID: {metadata.get("work_item_id")}
Title: {metadata.get("title")}
State: {metadata.get("state")}

{document}
""".strip()
    )


context = "\n\n".join(context_parts)


# ============================================================
# 5. Create prompt for Qwen
# ============================================================

prompt = f"""
You are an assistant for an application development team.

Answer the user's question using the Azure DevOps
requirements provided below.

Do not invent requirements that are not present in
the provided context.

If the context does not contain enough information
to answer the question, say that the available
requirements do not provide enough information.

User question:
{QUESTION}

Azure DevOps requirements:
{context}

Answer:
""".strip()


# ============================================================
# 6. Send context + question to Qwen
# ============================================================

print("\nSending context to Qwen...\n")

response = requests.post(
    f"{OLLAMA_URL}/api/generate",
    json={
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False
    }
)

response.raise_for_status()

answer = response.json()["response"]


# ============================================================
# 7. Display result
# ============================================================

print("=" * 60)
print("QUESTION")
print("=" * 60)

print(QUESTION)

print("\n" + "=" * 60)
print("RETRIEVED CONTEXT")
print("=" * 60)

print(context)

print("\n" + "=" * 60)
print("QWEN ANSWER")
print("=" * 60)

print(answer)