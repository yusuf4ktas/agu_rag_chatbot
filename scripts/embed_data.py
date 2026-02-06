import json
import os
import glob
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
import mimetypes
import torch

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'vector_db')
CHROMA_COLLECTION_NAME = "college_rag"

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

mimetypes.add_type("application/javascript", ".js")


def load_and_combine_data(data_dir):
    """
    Loads data from all .json files in the specified directory,
    combines them, and extracts text content.
    """
    all_documents = []

    # Load scraped web content
    scraped_json_path = os.path.join(data_dir, 'scraped_content.json')
    if os.path.exists(scraped_json_path):
        try:
            with open(scraped_json_path, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
                print(f"Loaded {len(scraped_data)} documents from {scraped_json_path}")
                all_documents.extend(scraped_data)
        except json.JSONDecodeError:
            print(f"Error reading {scraped_json_path}. File might be empty or malformed.")
        except Exception as e:
            print(f"An error occurred loading {scraped_json_path}: {e}")

    # Load parsed FAQ content
    faq_json_path = os.path.join(data_dir, 'parsed_faqs.json')
    if os.path.exists(faq_json_path):
        try:
            with open(faq_json_path, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
                print(f"Loaded {len(faq_data)} documents from {faq_json_path}")
                all_documents.extend(faq_data)
        except json.JSONDecodeError:
            print(f"Error reading {faq_json_path}. File might be empty or malformed.")
        except Exception as e:
            print(f"An error occurred loading {faq_json_path}: {e}")

    print(f"Total documents to process: {len(all_documents)}")
    return all_documents


def chunk_documents(documents):
    """
    Takes a list of document objects and splits the 'content'
    field into smaller chunks.
    Preserves metadata like source, page, paragraph, type, lang.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    all_chunks = []
    global_idx = 0  # ensure globally unique IDs

    for doc_idx, doc in enumerate(documents):
        if not doc.get('content'):
            print(f"Skipping document with no 'content' (Source: {doc.get('source', 'Unknown')})")
            continue

        # Split the text
        chunks = text_splitter.split_text(doc['content'])

        for chunk_idx, chunk_text in enumerate(chunks):
            # Build raw metadata
            meta_raw = {
                "source": doc.get('source', 'Unknown'),
                "page": doc.get('page'),
                "paragraph": doc.get('paragraph'),
                "type": doc.get('type'),
                "lang": doc.get('lang'),
            }

            metadata = {k: v for k, v in meta_raw.items() if v is not None}

            all_chunks.append({
                "text": chunk_text,
                "metadata": metadata,
                # Unique ID: global counter + doc index + chunk index
                "id": f"doc{doc_idx}_chunk{chunk_idx}_global{global_idx}",
            })

            global_idx += 1

    print(f"Total chunks created after splitting: {len(all_chunks)}")
    return all_chunks


def initialize_vector_db(db_dir, collection_name, embedding_model):
    """
    Initializes ChromaDB, creates a collection.
    """
    print(f"Initializing vector database at: {db_dir}")
    db_client = chromadb.PersistentClient(path=db_dir)

    print(f"Getting or creating ChromaDB collection: {collection_name}")
    collection = db_client.get_or_create_collection(
        name=collection_name
    )
    return collection


def load_embedding_model(model_name):
    """
    Loads the SentenceTransformer model from Hugging Face.
    """
    print(f"Loading embedding model: {model_name}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device for embeddings: {device}")

    model = SentenceTransformer(model_name, device=device)
    print("Embedding model loaded.")
    return model


def embed_and_store(collection, chunks, model, batch_size=32):
    """
    Generates embeddings for all chunks.
    Adds them to the ChromaDB collection.
    """
    print("Starting chunking, embedding, and storing process...")
    if not chunks:
        print("No chunks to process. Exiting.")
        return

    print(f"Total chunks to embed: {len(chunks)}")

    print("Generating embeddings... This may take a moment.")
    all_texts = [chunk["text"] for chunk in chunks]

    # For BGE-m3, it's recommended to normalize embeddings
    all_embeddings = model.encode(
        all_texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    print("Adding embeddings to the vector database...")

    embedding_lists = [emb.tolist() for emb in all_embeddings]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [chunk["id"] for chunk in chunks]
    documents_to_store = all_texts

    total_chunks = len(ids)
    for i in range(0, total_chunks, batch_size):
        batch_end = min(i + batch_size, total_chunks)

        batch_ids = ids[i:batch_end]
        batch_embeddings = embedding_lists[i:batch_end]
        batch_metadatas = metadatas[i:batch_end]
        batch_docs = documents_to_store[i:batch_end]

        collection.add(
            embeddings=batch_embeddings,
            documents=batch_docs,
            metadatas=batch_metadatas,
            ids=batch_ids
        )

    print("...Embeddings added successfully.")


def main():
    """
    Main execution pipeline.
    """
    print("--- Step 1: Loading and Combining Data ---")
    documents = load_and_combine_data(DATA_DIR)
    if not documents:
        print("No documents found. Please check your 'data' directory and JSON files.")
        return

    print("\n--- Step 2: Loading Embedding Model ---")
    model = load_embedding_model(EMBEDDING_MODEL_NAME)

    print("\n--- Step 3: Initializing Vector DB ---")
    collection = initialize_vector_db(VECTOR_DB_DIR, CHROMA_COLLECTION_NAME, model)

    print("\n--- Step 4: Chunking Documents ---")
    chunks = chunk_documents(documents)

    print("\n--- Step 5: Embedding and Storing ---")
    embed_and_store(collection, chunks, model)

    print("\n--- Success! ---")
    print(f"Data has been embedded and stored in ChromaDB.")
    print(f"Total documents: {len(documents)}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Database location: {VECTOR_DB_DIR}")


if __name__ == "__main__":
    main()
