# ingest.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents import Document
import os


class DocLoader:
    def __init__(self, user_id, api_key, file_path, persist_dir="./chromadb") -> None:
        self.user_id = user_id
        self.file_path = file_path
        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=[
                "\n\n",
                "\n",
                " ",
                ".",
                ",",
                "",
            ],
        )
        try:
            if os.path.exists(persist_dir):
                self.persist_directory = persist_dir
            else:
                os.mkdir(persist_dir)
                self.persist_directory = persist_dir
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Database Directory not found: {persist_dir}"
            ) from e
        except Exception as e:
            raise ValueError(f"Error during data ingestion: {e}") from e

    def ingest_document(self):
        self.delete_db(user_id=self.user_id)
        self.document_list: list[Document] = list()
        print(self.file_path)

        file_extension = os.path.splitext(self.file_path)[1].lower()

        if file_extension == ".pdf":
            self.loader = PyPDFLoader(self.file_path)
        elif file_extension in [".pptx", ".docx", ".txt"]:
            self.loader = UnstructuredURLLoader(urls=[self.file_path])
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        self.document_list.extend(
            self.loader.load_and_split(text_splitter=self.text_splitter)
        )

        for doc_data in self.document_list:
            doc_data.metadata = {"user_id": self.user_id}
            # if isinstance(doc_data.page_content, bytes):
            #     doc_data.page_content = doc_data.page_content.decode("utf-8")
            # elif isinstance(doc_data.page_content, str):
            #     doc_data.page_content = doc_data.page_content.encode("utf-8")

        self.docsearch: Chroma = Chroma.from_documents(
            self.document_list,
            self.embeddings,
            persist_directory=self.persist_directory,
        )

    def delete_db(self, user_id):
        self.pdfsearch: Chroma = Chroma(persist_directory="./chromadb")
        self.pdfsearch._collection.delete(where={"user_id": user_id})

    def __call__(self):
        self.ingest_document()