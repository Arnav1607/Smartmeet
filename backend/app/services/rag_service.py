import os
import openai
import chromadb
from flask import current_app
from app.services.ai_service import rag_chat
from app.services.encryption import decrypt

def get_openai_client():
    api_key = current_app.config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
    return openai.OpenAI(api_key=api_key)

def get_chroma_collection():
    """Get or create the persistent transcripts collection."""
    chroma_path = current_app.config.get('CHROMA_PATH')
    if not chroma_path:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        chroma_path = os.path.join(base_dir, '..', '..', 'instance', 'chroma_db')
        
    os.makedirs(chroma_path, exist_ok=True)
    client = chromadb.PersistentClient(path=chroma_path)
    return client.get_or_create_collection("transcripts")

def embed_text(text: str) -> list:
    """Generate vector embedding from OpenAI."""
    try:
        oai = get_openai_client()
        # Cap text length to avoid token limit issues
        clipped = text[:2000]
        res = oai.embeddings.create(model="text-embedding-3-small", input=clipped)
        return res.data[0].embedding
    except Exception as e:
        print(f"[Embedding Error] Failed to generate embedding: {e}")
        # Return a zero vector of dimension 1536 as fallback so indexing/querying doesn't crash
        return [0.0] * 1536

def index_transcript(meeting_id: str, entries: list):
    """Embed all transcript chunks for a meeting and store in persistent ChromaDB."""
    if not entries:
        return

    collection = get_chroma_collection()
    
    # Check if already indexed to avoid duplicates
    existing = collection.get(where={"meeting_id": meeting_id})
    if existing and existing['ids']:
        print(f"[RAG Index] Meeting {meeting_id} already indexed. Skipping.")
        return

    docs, ids, embeddings = [], [], []
    for i, e in enumerate(entries):
        text = f"{e['speaker']}: {e['text']}"
        vector = embed_text(text)
        
        docs.append(text)
        ids.append(f"{meeting_id}_{i}")
        embeddings.append(vector)
        
    if docs:
        collection.add(
            documents=docs,
            embeddings=embeddings,
            ids=ids,
            metadatas=[{"meeting_id": meeting_id}] * len(docs)
        )
        print(f"[RAG Index] Successfully indexed {len(docs)} chunks for meeting {meeting_id}")

def query_transcript(meeting_id: str, question: str, k: int = 5) -> str:
    """Query ChromaDB for relevant meeting chunks, then answer via GPT."""
    try:
        collection = get_chroma_collection()
        q_embedding = embed_text(question)
        
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=min(k, 10),
            where={"meeting_id": meeting_id}
        )
        
        chunks = results['documents'][0] if results and results['documents'] else []
        
        if not chunks:
            # Fallback to fetching transcripts directly from DB if Vector store returned empty
            from app.models import Transcript
            transcripts = Transcript.query.filter_by(meeting_id=meeting_id).limit(40).all()
            chunks = []
            for t in transcripts:
                try:
                    decrypted = decrypt(t.text_encrypted, t.iv)
                    chunks.append(f"{t.speaker}: {decrypted}")
                except Exception:
                    pass
                    
        if not chunks:
            return "No meeting conversation transcript was found to analyze."
            
        return rag_chat(question, chunks)
        
    except Exception as e:
        print(f"[RAG Query Error] Chroma query failed: {e}")
        # Fail gracefully by querying relational database transcripts as fallback
        try:
            from app.models import Transcript
            transcripts = Transcript.query.filter_by(meeting_id=meeting_id).limit(30).all()
            chunks = []
            for t in transcripts:
                try:
                    decrypted = decrypt(t.text_encrypted, t.iv)
                    chunks.append(f"{t.speaker}: {decrypted}")
                except Exception:
                    pass
            if chunks:
                return rag_chat(question, chunks)
        except Exception:
            pass
        return "An error occurred while retrieving meeting context. Please verify your OpenAI API key is configured."
