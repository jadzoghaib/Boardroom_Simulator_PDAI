import os
import chromadb

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

def build_mentor_kb():
    """Builds a local vector database of startup playbooks for the Mentor Agent."""
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name="startup_playbooks")
    
    playbooks = [
        {"id": "doc_1", "text": "If burn rate is too high relative to revenue, cut marketing spend immediately and focus on organic growth channels to extend runway."},
        {"id": "doc_2", "text": "For high-experience founders in SaaS, finding a strategic corporate partner is often better and faster than securing traditional VC funding."},
        {"id": "doc_3", "text": "A cash runway of less than 6 months requires an emergency bridge round or an aggressive product pivot towards short-term revenue."},
        {"id": "doc_4", "text": "In the Fintech sector, compliance costs inflate burn rate early. Counter VC skepticism by highlighting regulatory moats as a competitive advantage."}
    ]
    
    if collection.count() == 0:
        texts = [item["text"] for item in playbooks]
        ids = [item["id"] for item in playbooks]
        collection.add(documents=texts, ids=ids)
    
    return collection

def search_playbook(query: str, n_results: int = 1) -> str:
    """Searches the ChromaDB vector store for relevant business advice."""
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name="startup_playbooks")
    
    results = collection.query(query_texts=[query], n_results=n_results)
    if results and results['documents'] and len(results['documents'][0]) > 0:
        return results['documents'][0][0]
    return "No specific playbook strategy found."

if __name__ == "__main__":
    build_mentor_kb()
    print("Vector database populated successfully.")
