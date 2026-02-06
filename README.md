# AGU RAG Chatbot

This repository contains a Retrieval-Augmented Generation (RAG) chatbot designed to answer questions about Abdullah Gül University (AGU). The system leverages a knowledge base constructed from official AGU documents and web pages to provide accurate, fact-based answers in both English and Turkish.

## Features

*   **Fact-Based Answers:** Utilizes a RAG pipeline to ground responses in information from a curated knowledge base.
*   **Bilingual Support:** Processes queries and provides answers in both English and Turkish, with automatic language detection and translation capabilities.
*   **Source Citation:** Returns the sources used to generate an answer, allowing users to verify the information.
*   **Efficient Local Deployment:** Employs 4-bit model quantization (`bitsandbytes`) to run the generator model efficiently on consumer-grade GPUs.
*   **Web Interface:** Includes a simple and intuitive React-based frontend for interacting with the chatbot.

## Architecture

The project consists of three main components: a data ingestion pipeline, a FastAPI backend that serves the RAG model, and a React frontend.

1.  **Data Ingestion Pipeline (`/scripts`)**
    *   **Web Scraping (`scrape_web.py`):** Scrapes specified AGU web pages to gather textual content.
    *   **Document Parsing (`parse_faqs.py`):** Extracts text from PDF and DOCX files located in the `data/faq_docs` directory.
    *   **Embedding (`embed_data.py`):** The collected text is chunked and then converted into vector embeddings using the `BAAI/bge-m3` model. These embeddings are stored in a local **ChromaDB** vector database.

2.  **Backend API (`api.py`)**
    *   Built with **FastAPI**.
    *   Receives a user query and detects its language (English or Turkish).
    *   Encodes the query into an embedding and retrieves the most relevant context chunks from ChromaDB.
    *   Translates the context chunks to match the query's language using Helsinki-NLP models.
    *   Constructs a detailed prompt containing the retrieved context and the user's question.
    *   Uses the **`Qwen/Qwen2.5-1.5B-Instruct`** model (quantized to 4-bit) to generate a concise answer based *only* on the provided context.
    *   Returns the final answer along with the source documents.

3.  **Frontend (`/frontend`)**
    *   A single-page application built with **React** and **Vite**.
    *   Provides a user-friendly interface for asking questions, viewing answers, and seeing the corresponding sources.
    *   Features a chat history and a resources page for quick access to important AGU links.

## Tech Stack

*   **Backend**: Python, FastAPI
*   **Vector Database**: ChromaDB
*   **Frontend**: React, Vite, CSS
*   **AI Models**:
    *   **Embedding**: `BAAI/bge-m3` (via `sentence-transformers`)
    *   **Generator**: `Qwen/Qwen2.5-1.5B-Instruct` (via `transformers`)
    *   **Translation (TR-EN)**: `Helsinki-NLP/opus-mt-tr-en`
    *   **Translation (EN-TR)**: `Helsinki-NLP/opus-mt-en-trk`
*   **Quantization**: `bitsandbytes` (for 4-bit loading)

## Setup and Installation

### Prerequisites

*   Python 3.8+
*   Node.js and npm
*   (Recommended) An NVIDIA GPU with CUDA support for hardware acceleration. The application can run on CPU, but performance will be significantly slower.

### 1. Backend Setup

First, set up the data ingestion pipeline and the API server.

```bash
# Clone the repository
git clone https://github.com/yusuf4ktas/agu_rag_chatbot.git
cd agu_rag_chatbot

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `.\venv\Scripts\activate`

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Data Ingestion

The chatbot's knowledge base is built from files in `/data` and `/data/faq_docs`.

1.  **(Optional) Add Your Documents:** Place any relevant `.pdf` or `.docx` files into the `data/faq_docs/` directory.

2.  **Run Ingestion Scripts:** Execute the following scripts in order from the root directory.

    ```bash
    # Scrape predefined web pages
    python scripts/scrape_web.py

    # Parse local documents from data/faq_docs/
    python scripts/parse_faqs.py

    # Chunk, embed, and store all data in ChromaDB. This is a required step.
    python scripts/embed_data.py
    ```
    This will create a `vector_db` directory containing the knowledge base.

### 3. Run the Backend API

Once the data has been embedded, you can start the FastAPI server.

```bash
# Run the API server
uvicorn api:app --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`. The first time you run it, the models will be downloaded, which may take some time.

### 4. Frontend Setup

In a new terminal, set up and run the React frontend.

```bash
# Navigate to the frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173` (or another port if 5173 is in use).

## How to Use

1.  Ensure both the backend API and the frontend development server are running.
2.  Open your web browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
3.  Type your question about Abdullah Gül University into the input box and press Enter or click the send button.
4.  The answer will appear, along with the sources used to generate it.
5.  You can view your recent queries in the "History" tab and find useful links on the "Resources" tab.
