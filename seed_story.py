import chromadb

# Connect to local ChromaDB
client = chromadb.HttpClient(
    host="localhost",
    port=8000
)

# Create/get collection
collection = client.get_or_create_collection(
    name="azuredevops_stories"
)

print("Collection created:")
print(collection.name)