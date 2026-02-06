import os
from typing import List, Optional
import re

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    BitsAndBytesConfig,
)

import chromadb

VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), "vector_db")
CHROMA_COLLECTION_NAME = "college_rag"

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
GENERATOR_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

app = FastAPI(title="RAG Chatbot API")

# CORS configuration to allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global variables to hold models and DB connection
class AppComponents:
    db_collection = None
    embedding_model = None
    generator_tokenizer = None
    generator_model = None
    device = None

    # Translation models
    translator_tr_en_tokenizer = None
    translator_tr_en_model = None
    translator_en_tr_tokenizer = None
    translator_en_tr_model = None


components = AppComponents()


@app.on_event("startup")
def initialize_components():
    """
    Load all models and connect to the database on API startup.
    This ensures models are not reloaded on every request.
    """
    print("--- Initializing RAG components ---")

    components.device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {components.device}")

    # Connect to ChromaDB
    try:
        db_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        components.db_collection = db_client.get_collection(name=CHROMA_COLLECTION_NAME)
        print(f"Successfully connected to ChromaDB collection at: {VECTOR_DB_DIR}")
    except Exception as e:
        print(f"CRITICAL: Failed to connect to ChromaDB at {VECTOR_DB_DIR}.")
        print(f"Error: {e}")
        print(
            "Please ensure you have run 'python scripts/embed_data.py' first "
            "(and that it used the same path)."
        )
        return

    # Load Embedding Model (on CPU to save GPU for Qwen)
    try:
        components.embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME,
            device="cpu",
        )
        print(f"Embedding model loaded on CPU: {EMBEDDING_MODEL_NAME}")
    except Exception as e:
        print("CRITICAL: Failed to load embedding model.")
        print(f"Error: {e}")
        return

    # Load Generator Model & Tokenizer (Qwen, causal LM)
    try:
        components.generator_tokenizer = AutoTokenizer.from_pretrained(
            GENERATOR_MODEL_NAME
        )

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )

        components.generator_model = AutoModelForCausalLM.from_pretrained(
            GENERATOR_MODEL_NAME,
            quantization_config=bnb_config,
            device_map="auto",
        )

        if components.generator_tokenizer.eos_token_id is None:
            components.generator_tokenizer.eos_token = "</s>"

        print("Generator loaded (Qwen, 4-bit):", GENERATOR_MODEL_NAME)
    except Exception as e:
        print("CRITICAL: Failed to load generator model.")
        print(f"Error: {e}")
        return

    # Load Translation Models
    print("Loading translation models...")

    # Turkish → English
    try:
        components.translator_tr_en_tokenizer = AutoTokenizer.from_pretrained(
            "Helsinki-NLP/opus-mt-tr-en",
            use_fast=False,
        )
        components.translator_tr_en_model = AutoModelForSeq2SeqLM.from_pretrained(
            "Helsinki-NLP/opus-mt-tr-en",
        ).to("cpu")
        print("Loaded TR→EN translator.")
    except Exception as e:
        print(
            "WARNING: Failed to load TR→EN translator. "
            "Turkish contexts won't be translated to English."
        )
        print(f"Error: {e}")

    # English → Turkish
    try:
        components.translator_en_tr_tokenizer = AutoTokenizer.from_pretrained(
            "Helsinki-NLP/opus-mt-en-trk",
            use_fast=False,
        )
        components.translator_en_tr_model = AutoModelForSeq2SeqLM.from_pretrained(
            "Helsinki-NLP/opus-mt-en-trk",
        ).to("cpu")
        print("Loaded EN→TR translator.")
    except Exception as e:
        print(
            "WARNING: Failed to load EN→TR translator. "
            "English contexts won't be translated to Turkish."
        )
        print(f"Error: {e}")

    print("--- All components initialized successfully ---")


class SourceInfo(BaseModel):
    source: str
    page: Optional[int] = None
    paragraph: Optional[int] = None
    type: Optional[str] = None
    lang: Optional[str] = None


def retrieve_context(query, collection, model, n_results: int = 5):
    """
    Retrieve relevant chunks from ChromaDB.
    Returns:
      - context_chunks: list[str]
      - sources: list[SourceInfo-like dict]
    """
    if collection is None or model is None:
        raise HTTPException(status_code=500, detail="API not initialized correctly.")

    query_embedding = model.encode(
        query,
        convert_to_tensor=False,
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    context_chunks = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    sources: List[dict] = []
    seen = set()

    for meta in metadatas:
        src = meta.get("source", "Unknown")
        page = meta.get("page")
        paragraph = meta.get("paragraph")
        section_type = meta.get("type")
        lang = meta.get("lang")

        key = (src, page, paragraph, section_type, lang)
        if key in seen:
            continue
        seen.add(key)

        sources.append(
            {
                "source": src,
                "page": page,
                "paragraph": paragraph,
                "type": section_type,
                "lang": lang,
            }
        )

    return context_chunks, sources


def detect_lang(text: str) -> str:
    """
    Heuristic language detection:
    - If text looks like English (common English words), return 'en' even.
    - Otherwise, if it contains Turkish-specific characters, return 'tr'.
    - Default to 'en'.
    """
    if not text:
        return "en"

    lower = text.lower()

    english_keywords = {
        "who",
        "what",
        "where",
        "when",
        "why",
        "how",
        "is",
        "are",
        "do",
        "does",
        "did",
        "can",
        "could",
        "should",
        "would",
        "have",
        "has",
        "had",
        "university",
        "program",
        "mobility",
        "internship",
        "study",
        "traineeship",
        "exchange",
        "admitted",
        "application",
        "requirements",
    }

    tokens = re.findall(r"[a-zA-Z]+", lower)

    if any(tok in english_keywords for tok in tokens):
        return "en"

    turkish_chars = set("çğıöşüÇĞİÖŞÜ")
    if any(c in turkish_chars for c in text):
        return "tr"

    return "en"


def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate text between TR and EN using Helsinki-NLP models.
    If the correct translator isn't loaded, just return the original text.
    """
    if not text or src_lang == tgt_lang:
        return text

    if src_lang == "tr" and tgt_lang == "en":
        tok = components.translator_tr_en_tokenizer
        model = components.translator_tr_en_model
    elif src_lang == "en" and tgt_lang == "tr":
        tok = components.translator_en_tr_tokenizer
        model = components.translator_en_tr_model
    else:
        return text

    if tok is None or model is None:
        return text

    inputs = tok(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    ).to("cpu")

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
        )

    return tok.decode(outputs[0], skip_special_tokens=True).strip()


FALLBACK_MESSAGE = "I'm sorry, I don't have that information in my knowledge base."


def build_prompt(query: str, context_chunks: List[str]) -> str:
    context = "\n\n".join(context_chunks) if context_chunks else ""
    q_lang = detect_lang(query)

    language_rule = (
        "The user has asked this question in English, so you MUST answer in clear English.\n"
        if q_lang == "en"
        else "The user has asked this question in Turkish, so you MUST answer in clear Turkish.\n"
    )

    prompt = (
        "You are an assistant for Abdullah Gül University (AGU).\n"
        "You answer questions ONLY using the information in the context below.\n\n"
        "RULES:\n"
        "1. Use ONLY the information inside <context> ... </context>.\n"
        "2. Do NOT invent new facts.\n"
        f"3. {language_rule}"
        "4. Answer the question DIRECTLY and CONCISELY in 1–3 sentences.\n"
        "5. Do NOT give advice unless the question explicitly asks for advice.\n"
        "6. Do NOT talk about the context or about being an AI.\n\n"
        "<context>\n"
        f"{context}\n"
        "</context>\n\n"
        f"Question: {query}\n"
        "Answer:"
    )
    return prompt


def clean_generated_answer(raw: str) -> str:
    text = raw.strip()

    lower = text.lower()
    idx = lower.find("answer:")
    if idx != -1:
        text = text[idx + len("answer:") :].strip()

    if text.startswith(('"', "“")) and text.endswith(('"', "”")):
        text = text[1:-1].strip()

    return text


def generate_answer(prompt: str, tokenizer, model, device: str) -> str:
    """
    Generate a short, factual answer.
    """
    if tokenizer is None or model is None:
        raise HTTPException(status_code=500, detail="API not initialized correctly.")

    input_device = "cuda" if torch.cuda.is_available() else "cpu"

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=1024,
    ).to(input_device)

    with torch.inference_mode():
        output_sequences = model.generate(
            **inputs,
            max_new_tokens=96,
            temperature=0.0,
            top_p=1.0,
            do_sample=False,
            no_repeat_ngram_size=4,
            repetition_penalty=1.1,
            eos_token_id=tokenizer.eos_token_id,
        )

    raw_answer = tokenizer.decode(output_sequences[0], skip_special_tokens=True)
    return clean_generated_answer(raw_answer)


# --- API Endpoints ---


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]


@app.get("/")
def get_root():
    """Root endpoint for health check."""
    return {"status": "RAG API is running."}


@app.post("/chat", response_model=ChatResponse)
async def chat_with_rag(request: ChatRequest):
    try:
        # Retrieve original context from Chroma
        context_chunks, sources_raw = retrieve_context(
            request.query,
            components.db_collection,
            components.embedding_model,
        )

        if not context_chunks:
            print("No context retrieved; returning fallback directly.")
            return ChatResponse(answer=FALLBACK_MESSAGE, sources=[])

        # Detect user language
        question_lang = detect_lang(request.query)
        print(f"Detected question language: {question_lang}")

        # Translate each chunk if needed
        translated_chunks: List[str] = []
        for chunk in context_chunks:
            chunk_lang = detect_lang(chunk)

            if question_lang == "en" and chunk_lang == "tr":
                translated = translate_text(chunk, "tr", "en")
            elif question_lang == "tr" and chunk_lang == "en":
                translated = translate_text(chunk, "en", "tr")
            else:
                translated = chunk

            translated_chunks.append(translated)

        # Optional debug
        if translated_chunks:
            print("\n=== FIRST ORIGINAL CHUNK ===\n", context_chunks[0][:400])
            print("\n=== FIRST TRANSLATED CHUNK ===\n", translated_chunks[0][:400])

        prompt = build_prompt(request.query, translated_chunks)

        answer = generate_answer(
            prompt,
            components.generator_tokenizer,
            components.generator_model,
            components.device,
        )

        return ChatResponse(answer=answer, sources=sources_raw)

    except Exception as e:
        print(f"Error during chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
