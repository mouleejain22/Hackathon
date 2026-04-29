import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def load_knowledge_base(folder="knowledge_base"):
    documents = []
    if not os.path.exists(folder):
        print(f"Warning: folder '{folder}' not found!")
        return documents

    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                chunks = content.split("\n\n")
                for chunk in chunks:
                    chunk = chunk.strip()
                    if len(chunk) > 30:
                        documents.append(chunk)
    return documents

def build_index(documents):
    embeddings = model.encode(documents, show_progress_bar=False)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    return index

def search(query, documents, index, top_k=3):
    query_embedding = model.encode([query])
    distances, indices = index.search(
        np.array(query_embedding).astype('float32'), top_k
    )
    results = []
    for i in indices[0]:
        if i < len(documents):
            results.append(documents[i])
    return results

print("Loading knowledge base...")
documents = load_knowledge_base()
index = build_index(documents)
print(f"Loaded {len(documents)} knowledge chunks.")