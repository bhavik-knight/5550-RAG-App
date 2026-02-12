# RAG Application

A Retrieval-Augmented Generation (RAG) system for question-answering using PDF documents.

## Architecture

This RAG system uses:
- **Embeddings**: Jina AI (`jina-embeddings-v4`) - State-of-the-art embedding model
- **LLM**: Meta Llama-3.3-70B via Groq - Fast, free, and excellent for RAG tasks
- **Vector Store**: ChromaDB - Efficient similarity search
- **Framework**: LangChain - For orchestrating the RAG pipeline

## Project Structure

```
rag-app/
├── src/                    # Source code directory
│   ├── main.py            # Main application entry point
│   ├── config.py          # Configuration and API key management
│   ├── embedder.py        # Jina embedding model wrapper
│   ├── ingest.py          # PDF ingestion and vector store creation
│   └── rag_query.py       # RAG query engine
├── data/                  # Input PDF files
├── output/                # Query results and vector database
│   ├── chroma_db/        # ChromaDB vector store
│   └── results.txt       # Automated query results
├── run.py                # Main entry point script
├── .env                  # API keys (not in git)
├── pyproject.toml        # Project dependencies
└── README.md             # This file
```

## Setup

### 1. Install Dependencies

This project uses `uv` for dependency management:

```bash
uv sync
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```env
JINA_API_KEY=your_jina_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

**Get your API keys:**
- **Jina AI**: https://jina.ai/embeddings/ (free tier available)
- **Groq**: https://console.groq.com/keys (free tier with generous limits)

### 3. Add Your PDF Documents

Place your PDF files in the `data/` directory.

## Usage

The application has three modes:

### Automated Mode (Default)

Run predefined test queries and save results:

```bash
uv run python run.py
# or explicitly:
uv run python run.py --mode automated
```

Results are saved to `output/results.txt`.

### Ingest Mode

Process PDF documents and create the vector database:

```bash
uv run python run.py --mode ingest
```

This creates a ChromaDB vector store in `output/chroma_db/`.

### Interactive Query Mode

Ask questions interactively:

```bash
uv run python run.py --mode query
```

Type your questions and get answers with source citations. Type 'exit' to quit.

## How It Works

1. **Ingestion** (`ingest.py`):
   - Loads PDF documents from the `data/` directory
   - Splits text into chunks (1000 chars with 200 char overlap)
   - Creates embeddings using Jina AI
   - Stores in ChromaDB vector database

2. **Query** (`rag_query.py`):
   - Retrieves relevant document chunks based on query similarity
   - Sends context to Llama-3.3-70B for answer generation
   - Returns answer with source citations (filename and page numbers)
   - If answer is "I don't know", no sources are shown

## Features

- ✅ **Smart Citations**: Automatically extracts and formats source citations
- ✅ **Clean Output**: LLM answers without embedded citations (sources listed separately)
- ✅ **Unknown Handling**: Returns "I don't know" for questions outside the knowledge base
- ✅ **Fast Inference**: Groq provides extremely fast LLM responses
- ✅ **Free Tier**: Both Jina AI and Groq offer generous free tiers

## Example Output

```
Question: What is Crosswalk guards?
Answer: Crosswalk guards direct the movement of children along or across highways going to or from school. They signal drivers to stop by holding up a stop sign facing the vehicle. Drivers must obey crossing guards appointed and employed for this purpose.
Sources: DH-Chapter2.pdf (Page 7), DH-Chapter2.pdf (Page 6), DH-Chapter2.pdf (Page 3)
```

## Configuration

Edit `src/config.py` to customize:
- Data directory path
- Output directory path
- API key validation

Edit `src/ingest.py` to customize:
- Chunk size and overlap
- PDF processing parameters

Edit `src/rag_query.py` to customize:
- LLM model and parameters
- Retrieval settings
- Prompt template

## Dependencies

Key dependencies (managed via `pyproject.toml`):
- `langchain` - RAG framework
- `langchain-groq` - Groq LLM integration
- `langchain-chroma` - ChromaDB vector store
- `langchain-community` - Community integrations
- `chromadb` - Vector database
- `pypdf` - PDF processing
- `python-dotenv` - Environment variable management

## Troubleshooting

**Missing API Keys Error:**
- Ensure your `.env` file exists and contains valid API keys
- Check that the `.env` file is in the project root directory

**Vector Store Not Found:**
- Run ingestion first: `uv run python run.py --mode ingest`
- Ensure PDF files are in the `data/` directory

**Import Errors:**
- Run `uv sync` to install all dependencies
- Ensure you're running from the project root directory

## License

MIT License - See LICENSE file for details
