#!/usr/bin/env python3
"""
Main entry point for the RAG application.
Run this from the project root directory.
"""
import sys
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modular RAG Pipeline")
    parser.add_argument("--mode", choices=['ingest', 'query', 'automated'], default='automated', help="Mode to run: ingest (create DB), query (interactive), automated (run default questions)")
    
    args = parser.parse_args()
    
    # Show available modes info
    print(f"\nRAG Application - Running in '{args.mode}' mode")
    print("Available modes: --mode ingest | --mode query | --mode automated (default)\n")
    
    main(args.mode)
