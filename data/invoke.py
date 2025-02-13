# invoke.py
from langchain_core.documents import Document
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains.question_answering import load_qa_chain
from typing import List


class BaseInvoke:
    def __init__(self, api_key: str, user_id: str, prompt_template: str):
        self.api_key = api_key
        self.user_id = user_id
        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)
        self.embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=self.api_key
        )
        self.vectorstore = Chroma(
            persist_directory="./chromadb", embedding_function=self.embedding_function
        )
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"filter": {"user_id": user_id}}
        )
        self.prompt = PromptTemplate(
            input_variables=["chat_history", "human_input", "context"],
            template=prompt_template,
        )
        self.memory = ConversationBufferWindowMemory(
            k=4, memory_key="chat_history", input_key="human_input"
        )
        self.chain = load_qa_chain(
            self.llm, chain_type="stuff", memory=self.memory, prompt=self.prompt
        )

    def invoke(self, query: str | bytes) -> str:
        if isinstance(query, str):
            query = query.encode("utf-8")
        elif isinstance(query, bytes):
            query = query.decode("utf-8")
        retrieved_docs: list[Document] = self.retriever.invoke(query)
        self.response = self.chain(
            {"input_documents": retrieved_docs, "human_input": query},
            return_only_outputs=True,
        )
        return self.response["output_text"]


class PDFInvoke(BaseInvoke):
    def __init__(self, api_key: str, user_id: str):
        pdf_prompt_template = """
You are provided with a PDF document as context. Use the information in this document to answer the query as accurately as possible.
1. First, determine if the context provided is relevant to the input query.
2. If relevant, use the context to answer the query directly.
3. If not relevant, use your own knowledge or indicate that you cannot answer based on the provided context.

### Context:
{context}

### Conversation:
{chat_history}

### Query:
Human: {human_input}
AI:"""
        super().__init__(api_key, user_id, pdf_prompt_template)


class DOCXInvoke(BaseInvoke):
    def __init__(self, api_key: str, user_id: str):
        docx_prompt_template = """
You are provided with a DOCX document as context. Utilize the content in this document to answer the query as precisely as possible.
1. Evaluate if the provided context is relevant to the input query.
2. If relevant, use the context to formulate your answer.
3. If not relevant, rely on your own knowledge or state that you cannot answer based on the provided context.

### Context:
{context}

### Conversation:
{chat_history}

### Query:
Human: {human_input}
AI:""
        """
        super().__init__(api_key, user_id, docx_prompt_template)


class TXTInvoke(BaseInvoke):
    def __init__(self, api_key: str, user_id: str):
        txt_prompt_template = """
You are provided with a TXT document as context. Leverage the information in this text document to respond to the query accurately.
1. Assess if the context is relevant to the query.
2. If relevant, use the context to generate your answer.
3. If not relevant, use your own knowledge or indicate your inability to answer based on the context provided.

### Context:
{context}

### Conversation:
{chat_history}

### Query:
Human: {human_input}
AI:""
        """
        super().__init__(api_key, user_id, txt_prompt_template)


class PPTXInvoke(BaseInvoke):
    def __init__(self, api_key: str, user_id: str):
        pptx_prompt_template = """
You are provided with a PPTX document as context. Use the content in this presentation to answer the query as accurately as possible.
1. Determine if the context is relevant to the input query.
2. If relevant, use the context to answer the query directly.
3. If not relevant, rely on your own knowledge or state that you cannot answer based on the provided context.

### Context:
{context}

### Conversation:
{chat_history}

### Query:
Human: {human_input}
AI:"""
        super().__init__(api_key, user_id, pptx_prompt_template)