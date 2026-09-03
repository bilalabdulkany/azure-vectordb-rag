import os
import requests
import chromadb
from bs4 import BeautifulSoup


# ============================================================
# Configuration
# ============================================================

ORGANIZATION = "olakara"
PROJECT = "VectorPOC"

AZDO_PAT = os.getenv("AZDO_PAT")

AZDO_BASE_URL = (
    f"https://dev.azure.com/"
    f"{ORGANIZATION}/{PROJECT}"
)

OLLAMA_URL = "http://localhost:11434"

EMBEDDING_MODEL = "qwen3-embedding:0.6b"

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

COLLECTION_NAME = "azuredevops_stories"


if not AZDO_PAT:
    raise Exception(
        "AZDO_PAT environment variable is not set."
    )


# ============================================================
# Azure DevOps authentication
# ============================================================

auth = ("", AZDO_PAT)


# ============================================================
# Connect to ChromaDB
# ============================================================

print("Connecting to ChromaDB...")

chroma_client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)

print(
    f"ChromaDB collection: {COLLECTION_NAME}"
)

print(
    f"Existing documents: {collection.count()}"
)


# ============================================================
# 1. Get User Story IDs using WIQL
# ============================================================

print("\nQuerying Azure DevOps...")

wiql = {
    "query": f"""
        SELECT
            [System.Id]
        FROM WorkItems
        WHERE
            [System.TeamProject] = '{PROJECT}'
            AND [System.WorkItemType] = 'User Story'
        ORDER BY [System.Id]
    """
}


wiql_url = (
    f"{AZDO_BASE_URL}"
    f"/_apis/wit/wiql"
    f"?api-version=7.1"
)


response = requests.post(
    wiql_url,
    json=wiql,
    auth=auth
)

response.raise_for_status()

wiql_result = response.json()


work_item_ids = [
    item["id"]
    for item in wiql_result.get(
        "workItems",
        []
    )
]


print(
    f"Found {len(work_item_ids)} User Stories."
)


if not work_item_ids:
    print("No User Stories found.")
    exit()


# ============================================================
# 2. Retrieve work items in batches
# ============================================================

FIELDS = [
    "System.Id",
    "System.Title",
    "System.Description",
    "System.State",
    "System.WorkItemType",
    "System.AssignedTo",
    "System.Tags",
    "System.AreaPath",
    "System.IterationPath",
    "System.CreatedDate",
    "System.ChangedDate"
]


def get_display_name(value):

    if isinstance(value, dict):
        return value.get(
            "displayName",
            ""
        )

    return value or ""


def html_to_text(value):

    if not value:
        return ""

    soup = BeautifulSoup(
        value,
        "html.parser"
    )

    return soup.get_text(
        "\n",
        strip=True
    )


# Azure DevOps supports up to 200 IDs per batch
for batch_start in range(
    0,
    len(work_item_ids),
    200
):

    batch_ids = work_item_ids[
        batch_start:
        batch_start + 200
    ]

    print(
        f"\nRetrieving stories "
        f"{batch_start + 1}-"
        f"{batch_start + len(batch_ids)}..."
    )


    batch_url = (
        f"{AZDO_BASE_URL}"
        f"/_apis/wit/workitemsbatch"
        f"?api-version=7.1"
    )


    batch_body = {
        "ids": batch_ids,
        "fields": FIELDS
    }


    response = requests.post(
        batch_url,
        json=batch_body,
        auth=auth,
        headers={
            "Content-Type": "application/json"
        }
    )

    response.raise_for_status()

    work_items = response.json()["value"]


    # ========================================================
    # 3. Process every User Story
    # ========================================================

    for item in work_items:

        fields = item["fields"]

        work_item_id = item["id"]

        title = fields.get(
            "System.Title",
            ""
        )

        description = html_to_text(
            fields.get(
                "System.Description",
                ""
            )
        )

        state = fields.get(
            "System.State",
            ""
        )

        work_item_type = fields.get(
            "System.WorkItemType",
            ""
        )

        tags = fields.get(
            "System.Tags",
            ""
        )

        assigned_to = get_display_name(
            fields.get(
                "System.AssignedTo"
            )
        )

        area_path = fields.get(
            "System.AreaPath",
            ""
        )

        iteration_path = fields.get(
            "System.IterationPath",
            ""
        )

        created_date = fields.get(
            "System.CreatedDate",
            ""
        )

        changed_date = fields.get(
            "System.ChangedDate",
            ""
        )


        # ====================================================
        # 4. Build the document for semantic search
        # ====================================================

        document_parts = [
            f"Title: {title}",
            "",
            "Description:",
            description
        ]


        document = "\n".join(
            document_parts
        ).strip()


        # ====================================================
        # 5. Generate embedding using Ollama
        # ====================================================

        embedding_response = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": document
            }
        )

        embedding_response.raise_for_status()

        embedding = (
            embedding_response
            .json()["embeddings"][0]
        )


        # ====================================================
        # 6. Store in ChromaDB
        # ====================================================

        metadata = {
            "work_item_id": work_item_id,
            "work_item_type": work_item_type,
            "title": title,
            "state": state,
            "tags": tags,
            "assigned_to": assigned_to,
            "area_path": area_path,
            "iteration_path": iteration_path,
            "created_date": created_date,
            "changed_date": changed_date
        }


        collection.upsert(
            ids=[str(work_item_id)],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata]
        )


        print(
            f"Indexed #{work_item_id}: "
            f"{title}"
        )


print("\n================================")
print("Azure DevOps ingestion complete")
print("================================")

print(
    f"Total documents in ChromaDB: "
    f"{collection.count()}"
)