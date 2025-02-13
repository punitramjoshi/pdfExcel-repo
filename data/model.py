# invoke.py
from data.ingest import DocLoader
from data.invoke import PDFInvoke, DOCXInvoke, TXTInvoke, PPTXInvoke

from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from typing import List
import os
from dotenv import load_dotenv

load_dotenv(override=True)


class RAG:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=self.api_key)
        self.embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=self.api_key
        )

    def load_db(self, file_path, user_id):
        try:
            self.delete_db(user_id)
        except:
            pass
        self.docloader = DocLoader(
            user_id=user_id, file_path=file_path, api_key=self.api_key
        )
        self.vectorsearch = self.docloader()

    def format_docs(self, docs: list[Document]):
        return "\n\n".join(doc.page_content for doc in docs)

    def invoke(self, user_id, query: str | bytes, file_extension: str):
        if file_extension == "pdf":
            invoker = PDFInvoke(api_key=self.api_key, user_id=user_id)
        elif file_extension == "docx":
            invoker = DOCXInvoke(api_key=self.api_key, user_id=user_id)
        elif file_extension == "pptx":
            invoker = PPTXInvoke(api_key=self.api_key, user_id=user_id)
        elif file_extension == "txt":
            invoker = TXTInvoke(api_key=self.api_key, user_id=user_id)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        retrieved_docs: List[Document] = invoker.retriever.invoke(query)
        print(retrieved_docs)

        self.response = invoker.chain(
            {"input_documents": retrieved_docs, "human_input": query},
            return_only_outputs=True,
        )
        return self.response["output_text"]

    def delete_db(self, user_id, persist_directory: str = "./chromadb"):
        self.pdfsearch: Chroma = Chroma(persist_directory=persist_directory)
        self.pdfsearch._collection.delete(where={"user_id": user_id})