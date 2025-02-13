# RAG Document & Excel Query System

This project provides a Retrieval Augmented Generation (RAG) system for querying documents and Excel spreadsheets using natural language. It leverages LangChain, OpenAI models, and vector stores to ingest various file formats (PDF, DOCX, PPTX, TXT, and Excel) and answer user queries based on the contents of those files. In addition, it offers an advanced Excel module that refines user queries and, if necessary, converts Python Matplotlib visualization code into React (Recharts) code for interactive web-based charts.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Workflow](#workflow)
- [Endpoints and Features](#endpoints-and-features)
- [Installation and Setup](#installation-and-setup)
- [Execution and Usage](#execution-and-usage)
- [License](#license)

---

## Overview

The system is built as a Flask web application exposing multiple REST endpoints. It supports:

- **Document Ingestion**: Reads files (e.g., PDFs, PPTX, DOCX, TXT) and ingests them into a vector store (using Chroma) for semantic search.
- **Query Invocation**: Answers natural language queries by retrieving relevant document chunks and using language models to generate responses.
- **Excel Querying**: Processes Excel files with Pandas, refines queries based on metadata, and even converts visualization code from Python to JavaScript (React with Recharts).
- **Database Management**: Provides functionality to load and delete user-specific databases.

---

## Architecture

The project is organized into several modules:

### 1. **Flask API**
- **File**: Main application (e.g., `app.py`)
- **Responsibility**:  
  - Exposes REST endpoints for database loading (`/load_db`), query invocation (`/pdf_invoke`, `/excel_invoke`), and database deletion (`/delete_db`).
  - Routes incoming requests to appropriate backend processes.

### 2. **Document Ingestion**
- **File**: `ingest.py`
- **Key Component**: `DocLoader`
- **Responsibility**:
  - Reads various document types (PDF, PPTX, DOCX, TXT).
  - Splits text into manageable chunks using a recursive text splitter.
  - Converts file content into LangChain `Document` objects.
  - Ingests the documents into a persistent Chroma vector store with user-specific metadata.

### 3. **Query Invocation**
- **File**: `invoke.py` (two parts)
- **Key Components**:
  - **BaseInvoke and File-Specific Invokers**: Specialized classes for PDF, DOCX, TXT, and PPTX that build prompt templates and run QA chains using LangChain.
  - **RAG Class**:  
    - Acts as the main orchestrator.
    - Loads the database via the `DocLoader`.
    - Uses the appropriate invoker based on file type to retrieve relevant documents and answer queries.

### 4. **Excel Query and Visualization Module**
- **File**: `excel_model.py`
- **Key Component**: `ExcelBot`
- **Responsibility**:
  - Loads Excel files into Pandas DataFrames.
  - Cleans and processes column names and data.
  - Extracts metadata (columns, unique value pairs, sample data) to aid query refinement.
  - Refines user queries using a combination of system and human prompts.
  - Detects if the query requires visualization; if so, generates Matplotlib code and converts it to Recharts (React) code using an LLM.
  - Returns refined answers or visualization code alongside JSON data representation of the Excel content.

---

## Workflow

### **1. Loading the Database**
- **Endpoint**: `/load_db`
- **Process**:
  1. The user sends a POST request with `user_id` and `file_path`.
  2. The Flask API checks for supported file formats.
  3. For text-based files, the `DocLoader` in `ingest.py` loads and splits the document, then indexes it into a Chroma vector store.
  4. For Excel files, the `ExcelBot` in `excel_model.py` loads the spreadsheet and prepares metadata.

### **2. Querying the Database**
- **Document Querying**:
  - **Endpoint**: `/pdf_invoke`
  - The system uses the `RAG` class to:
    1. Determine the file type.
    2. Retrieve relevant document chunks using a vector search.
    3. Answer the query using a language model (LLM) with the context from the documents.
- **Excel Querying**:
  - **Endpoint**: `/excel_invoke`
  - The `ExcelBot`:
    1. Loads and cleans the Excel file.
    2. Extracts metadata (columns, unique values, sample rows).
    3. Refines the natural language query based on the metadata.
    4. If visualization is detected, generates Matplotlib code and converts it into Recharts (React) code.
    5. Returns either a textual answer or visualization code with JSON data for chart rendering.

### **3. Deleting the Database**
- **Endpoint**: `/delete_db`
- **Process**:
  1. The user sends a POST request with `user_id`.
  2. The system deletes all entries in the vector store (Chroma) associated with that `user_id`.

---

## Endpoints and Features

| **Endpoint**      | **Method** | **Description** |
| ----------------- | ---------- | --------------- |
| `/load_db`        | POST       | Load a document/Excel file into the system (supported formats: pptx, ppt, doc, docx, pdf, txt, text, md). |
| `/pdf_invoke`     | POST       | Invoke a query on a loaded PDF (or similar text-based document) and receive an answer based on the document content. |
| `/excel_invoke`   | POST       | Query an Excel file. The system refines the query using metadata and, if needed, returns visualization code in React (Recharts) along with JSON data. |
| `/delete_db`      | POST       | Delete the database (vector store) associated with the given `user_id`. |

---

## Installation and Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/your-project.git
   cd your-project
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   - Create a `.env` file in the project root.
   - Set your OpenAI API key and any other required configurations:
     ```
     OPENAI_API_KEY=your_openai_api_key
     ```

5. **Directory Setup**
   - Ensure a directory (default `./chromadb`) exists or is creatable for storing the vector store.

---

## Execution and Usage

1. **Run the Flask Server**
   ```bash
   python app.py
   ```
   - The server will start in debug mode (if enabled) and listen on the default port (e.g., 5000).

2. **Loading a Document**
   - **Request**: POST to `/load_db`
   - **Payload**:
     ```json
     {
       "user_id": "user123",
       "file_path": "path/to/document.pdf"
     }
     ```
   - The document is ingested, split into chunks, and stored in the vector database.

3. **Querying a Document**
   - **Request**: POST to `/pdf_invoke`
   - **Payload**:
     ```json
     {
       "user_id": "user123",
       "query": "What are the main topics discussed in the document?"
     }
     ```
   - The system retrieves relevant document chunks and returns an answer.

4. **Querying an Excel File**
   - **Request**: POST to `/excel_invoke`
   - **Payload**:
     ```json
     {
       "file_path": "path/to/spreadsheet.xlsx",
       "query": "Show me the sales figures for each region.",
       "sheet_name": "0"
     }
     ```
   - The `ExcelBot` refines the query using metadata, checks for visualization requests, and if applicable, converts visualization code to React (Recharts).

5. **Deleting a Database**
   - **Request**: POST to `/delete_db`
   - **Payload**:
     ```json
     {
       "user_id": "user123"
     }
     ```
   - The vector store entries associated with the user are deleted.

---

## License

This project is licensed under the MIT License.

---

By following the steps above, you can set up and run the project locally, load documents, perform natural language queries, and even generate visualization code from Excel data. This system combines modern NLP techniques with vector-based document retrieval to provide rich, context-aware responses to user queries.