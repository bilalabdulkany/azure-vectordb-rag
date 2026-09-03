# Azure DevOps → Ollama → ChromaDB Local RAG POC

This README documents the local RAG proof of concept built around:

- Azure DevOps User Stories
- Ollama
- Qwen3 4B
- Qwen3 Embedding 0.6B
- ChromaDB
- Python
- Postman

The goal is to retrieve relevant Azure DevOps requirements from ChromaDB and use Qwen3 to answer questions using those requirements as context.

## 1. Architecture

```text
Azure DevOps
     │ REST API
     ▼
Python Ingestion
     │
     ├── WIQL → User Story IDs
     ├── Work Items Batch API → Story data
     └── Clean/prepare documents
             │
             ▼
      Ollama Embeddings
      qwen3-embedding:0.6b
             │
             ▼
          ChromaDB
             │
        Semantic Search
             │
             ▼
       Relevant Stories
             │
             ▼
          Qwen3 4B
             │
             ▼
           Answer
```

## 2. Hardware

The development machine has approximately:

- System RAM: 8 GB
- NVIDIA GeForce MX330: 2 GB VRAM
- Intel UHD Graphics: 1 GB reported adapter memory

Because the MX330 has limited VRAM, Ollama is configured to run the LLM on CPU.

## 3. Models

### Qwen3 4B — LLM

Used for final answer generation.

Install:

```powershell
ollama pull qwen3:4b
```

Test:

```powershell
ollama run qwen3:4b
```

### Qwen3 Embedding 0.6B

Used to convert requirements and questions into vectors.

Install:

```powershell
ollama pull qwen3-embedding:0.6b
```

Check:

```powershell
ollama list
```

Expected models:

```text
qwen3:4b
qwen3-embedding:0.6b
```

Do not use the LLM model as the embedding model.

```text
qwen3-embedding:0.6b
Text → Vector

qwen3:4b
Context + Question → Answer
```

## 4. Ollama CPU Configuration

Set permanently for the current Windows user:

```powershell
[Environment]::SetEnvironmentVariable(
    "OLLAMA_LLM_LIBRARY",
    "cpu",
    "User"
)
```

Open a new PowerShell and verify:

```powershell
echo $env:OLLAMA_LLM_LIBRARY
```

Expected:

```text
cpu
```

## 5. Store Ollama Models on D:

Recommended location:

```text
D:\AI\Ollama\Models
```

Set:

```powershell
[Environment]::SetEnvironmentVariable(
    "OLLAMA_MODELS",
    "D:\AI\Ollama\Models",
    "User"
)
```

Verify:

```powershell
echo $env:OLLAMA_MODELS
```

Expected:

```text
D:\AI\Ollama\Models
```

If models were already downloaded on C:, copy the existing model directory before deleting the original:

```powershell
robocopy "$env:USERPROFILE\.ollama\models" "D:\AI\Ollama\Models" /E
```

Verify that Ollama can run the copied models before deleting the C: copy.

## 6. ChromaDB

Recommended data directory:

```text
D:\AI\ChromaDB\data
```

Create it:

```powershell
mkdir D:\AI\ChromaDB\data
```

Start ChromaDB:

```powershell
chroma run --path D:\AI\ChromaDB\data
```

ChromaDB should be available at:

```text
http://localhost:8000
```

Keep this terminal running.

### Test with Postman

```text
GET http://localhost:8000/api/v2/heartbeat
```

No authentication is required.

## 7. Azure DevOps Project

Current POC:

```text
Organization: olakara
Project: VectorPOC
Team: VectorPOC Team
Work Item Type: User Story
```

Backlog URL:

```text
https://olakara.visualstudio.com/VectorPOC/_backlogs/backlog/VectorPOC%20Team/Stories
```

REST API uses:

```text
https://dev.azure.com/olakara/VectorPOC/
```

## 8. Azure DevOps PAT

Create a Personal Access Token with:

```text
Work Items → Read
```

Do not hard-code the PAT.

Set it as a Windows user environment variable:

```powershell
[Environment]::SetEnvironmentVariable(
    "AZDO_PAT",
    "YOUR_AZURE_DEVOPS_PAT",
    "User"
)
```

Open a new PowerShell after setting it.

Verify:

```powershell
echo $env:AZDO_PAT
```

Do not share the token.

## 9. Test Azure DevOps with Postman

### Query User Story IDs

Method:

```text
POST
```

URL:

```text
https://dev.azure.com/olakara/VectorPOC/_apis/wit/wiql?api-version=7.1
```

Authorization:

```text
Basic Auth

Username: pat
Password: YOUR_PAT
```

Body:

```json
{
  "query": "SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType] FROM WorkItems WHERE [System.TeamProject] = 'VectorPOC' AND [System.WorkItemType] = 'User Story' ORDER BY [System.Id]"
}
```

The response returns the work item IDs.

Example:

```json
{
    "workItems": [
        {
            "id": 842,
            "url": "https://dev.azure.com/..."
        }
    ]
}
```

### Retrieve an individual Story

Example:

```text
GET
https://dev.azure.com/olakara/VectorPOC/_apis/wit/workitems/842?api-version=7.1
```

A targeted request:

```text
GET
https://dev.azure.com/olakara/VectorPOC/_apis/wit/workitems/842?fields=System.Id,System.Title,System.Description,System.State,System.Tags,System.AssignedTo,System.AreaPath,System.IterationPath&api-version=7.1
```

Story 842 was successfully retrieved with:

```text
ID: 842
Title: Display New Employee Form
State: New
Area: VectorPOC
Iteration: VectorPOC
Assigned To: Abdel Raoof
```

Description:

```text
As an user when I click on New button, I want to see
the New Employee Form so that I can enter details of
the new employee.
```

### Bulk retrieval

Use:

```text
POST
https://dev.azure.com/olakara/VectorPOC/_apis/wit/workitemsbatch?api-version=7.1
```

Example:

```json
{
    "ids": [842],
    "fields": [
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
}
```

The ingestion process uses batches of up to 200 IDs.

## 10. Python Environment

Recommended directory:

```text
D:\AI\ChromaDB
```

Create a virtual environment:

```powershell
cd D:\AI\ChromaDB
python -m venv venv
```

Activate:

```powershell
.\venv\Scripts\activate
```

Install dependencies:

```powershell
pip install chromadb requests beautifulsoup4
```

## 11. First ChromaDB Test

A test collection was created:

```text
azuredevops_stories
```

Story 842 was embedded using:

```text
POST http://localhost:11434/api/embed
```

Body:

```json
{
    "model": "qwen3-embedding:0.6b",
    "input": "Display New Employee Form. As an user when I click on New button, I want to see the New Employee Form so that I can enter details of the new employee."
}
```

The resulting vector was stored in ChromaDB with ID:

```text
842
```

Metadata included:

```json
{
    "work_item_id": 842,
    "work_item_type": "User Story",
    "state": "New",
    "area_path": "VectorPOC",
    "iteration_path": "VectorPOC",
    "assigned_to": "Abdel Raoof"
}
```

## 12. Semantic Search

Example question:

```text
How can I create a new employee?
```

Flow:

```text
Question
   ↓
qwen3-embedding:0.6b
   ↓
Question Vector
   ↓
ChromaDB
   ↓
Similar Stories
```

The important point is that semantic search does not require exact keyword matches.

For example, a question about creating an employee can retrieve stories about:

```text
Display New Employee Form
Save New Employee
Validate Employee Information
Generate Employee Number
```

## 13. End-to-End RAG

The complete flow is:

```text
User Question
      │
      ▼
Ollama Embedding
      │
      ▼
Question Vector
      │
      ▼
ChromaDB
      │
      ▼
Top Relevant Stories
      │
      ▼
Build Context
      │
      ▼
Qwen3 4B
      │
      ▼
Final Answer
```

Example:

```text
Question:
How can I create a new employee?
```

Retrieved context can contain:

```text
Work Item ID: 842
Title: Display New Employee Form

As a HR user, I want to open the New Employee Form
by clicking the New button, so that I can enter details
for a new employee.
```

The context is supplied to Qwen3.

The prompt should instruct Qwen3 to:

- Answer using the supplied Azure DevOps requirements.
- Not invent requirements that are not present.
- Say when the available context is insufficient.

## 14. Bulk Azure DevOps → ChromaDB Ingestion

The ingestion service should perform:

```text
1. Execute WIQL
2. Get all User Story IDs
3. Retrieve complete work items
4. Extract useful fields
5. Remove HTML from descriptions
6. Build searchable documents
7. Generate embeddings with Ollama
8. Upsert documents into ChromaDB
```

Recommended document:

```text
Title:
Display New Employee Form

Description:
As a HR user, I want to open the New Employee Form
by clicking the New button, so that I can enter details
for a new employee.

Acceptance Criteria:
1. The New button is visible on the Employee List page.
2. Clicking New opens the New Employee Form.
3. The form contains fields for employee information.
4. The user can cancel and return to the Employee List.
```

Metadata:

```json
{
    "work_item_id": 842,
    "work_item_type": "User Story",
    "title": "Display New Employee Form",
    "state": "New",
    "tags": "",
    "assigned_to": "Abdel Raoof",
    "area_path": "VectorPOC",
    "iteration_path": "VectorPOC"
}
```

## 15. Why `upsert` Is Important

Use the Azure DevOps work item ID as the ChromaDB ID:

```text
Azure DevOps       ChromaDB
----------------------------
842                "842"
843                "843"
844                "844"
```

Use:

```python
collection.upsert(
    ids=[str(work_item_id)],
    documents=[document],
    embeddings=[embedding],
    metadatas=[metadata]
)
```

This prevents duplicates when ingestion is run again.

If Story 842 changes:

```text
Azure DevOps Story 842
        ↓
Changed document
        ↓
New embedding
        ↓
ChromaDB upsert
        ↓
Existing 842 updated
```

## 16. Recommended Project Structure

```text
D:\AI\
│
├── Ollama\
│   └── Models\
│
└── ChromaDB\
    │
    ├── data\
    ├── venv\
    ├── azuredevops_ingest.py
    ├── seed_story.py
    ├── search_story.py
    └── rag_test.py
```

## 17. Running the System

### Terminal 1 — Ollama

The Ollama Windows application should be running.

Verify:

```powershell
ollama list
```

Expected:

```text
qwen3:4b
qwen3-embedding:0.6b
```

### Terminal 2 — ChromaDB

```powershell
chroma run --path D:\AI\ChromaDB\data
```

### Terminal 3 — Ingestion

```powershell
cd D:\AI\ChromaDB
.\venv\Scripts\activate

python azuredevops_ingest.py
```

### Terminal 4 — RAG question

```powershell
cd D:\AI\ChromaDB
.\venv\Scripts\activate

python rag_test.py
```

## 18. Current POC Status

```text
Azure DevOps REST API             ✓
Azure DevOps WIQL                 ✓
Retrieve User Story 842           ✓
Postman                           ✓
Ollama                            ✓
Qwen3 4B                          ✓
CPU-only Ollama                   ✓
Qwen3 Embedding 0.6B             ✓
ChromaDB                          ✓
ChromaDB heartbeat                ✓
Embedding generation              ✓
Story 842 insertion               ✓
Semantic ChromaDB search          ✓
ChromaDB → Qwen RAG test          ✓
```

## 19. Next Improvements

### 19.1 Acceptance Criteria and Custom Fields

Inspect the real Azure DevOps work item fields and include important fields such as:

```text
Description
Acceptance Criteria
Business Value
Priority
Story Points
Tags
Area Path
Iteration Path
```

Custom fields should be confirmed from the actual project before adding them to the ingestion script.

### 19.2 Incremental Synchronization

Do not re-embed the entire backlog every time.

Use:

```text
System.ChangedDate
```

Conceptually:

```text
Azure DevOps
     ↓
Changed since last sync?
     │
     ├── No → Skip
     │
     └── Yes
          ↓
       Re-embed
          ↓
       ChromaDB upsert
```

### 19.3 Deletions

The synchronization process should eventually handle:

```text
New Story       → Insert
Changed Story   → Update
Deleted Story   → Delete
```

For example:

```python
collection.delete(
    ids=["842"]
)
```

### 19.4 Chunking

Small User Stories can be one document.

Large requirements should be split into chunks:

```text
Story
 ├── Description chunk
 ├── Acceptance Criteria chunk 1
 ├── Acceptance Criteria chunk 2
 └── Technical Notes chunk
```

Each chunk should retain the Azure DevOps work item metadata.

### 19.5 ASP.NET Core Integration

After the Python POC is stable, the RAG process can be integrated with ASP.NET Core:

```text
Angular
   │
   ▼
ASP.NET Core API
   │
   ├──────────────► Ollama
   │                 ├── Embeddings
   │                 └── Qwen3
   │
   └──────────────► ChromaDB
                     └── Semantic Search
```

The Python ingestion service can remain separate.

## 20. Final Target Architecture

```text
                         ┌───────────────────┐
                         │   Azure DevOps    │
                         │                   │
                         │ User Stories      │
                         │ Requirements      │
                         └─────────┬─────────┘
                                   │
                                   │ REST API
                                   ▼
                         ┌───────────────────┐
                         │ Ingestion Service │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │ Ollama Embeddings │
                         │                   │
                         │ qwen3-embedding   │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │     ChromaDB      │
                         │                   │
                         │ Vectors           │
                         │ Documents         │
                         │ Metadata          │
                         └─────────┬─────────┘
                                   │
                                   │ Semantic Search
                                   ▼
┌─────────────┐           ┌───────────────────┐
│   Angular   │──────────►│   ASP.NET Core    │
└─────────────┘           └─────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │     Ollama       │
                           │     Qwen3 4B     │
                           └────────┬─────────┘
                                    │
                                    ▼
                                  Answer
```

## 21. Core Design Principle

```text
Azure DevOps = Source of truth
ChromaDB     = Searchable vector knowledge base
Embedding    = Semantic representation
Qwen3        = Answer generation
ASP.NET Core = Application/API layer
Angular      = User interface
```
