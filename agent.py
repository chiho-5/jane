from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, SummaryIndex, Settings
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from web_search import WebSearchFeature
from huggingface_hub import InferenceClient
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core import ServiceContext,set_global_service_context
import os


class SpaceAI:
    def __init__(self, data_directory, query, mode,llm_model="mistralai/Mistral-7B-Instruct-v0.3"):
        self.data_directory = data_directory
        self.llm_model = llm_model
        self.hf_token = "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"
        self.query = query
        self.web_search = WebSearchFeature()
        self.mode = mode
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
        self.user_sessions = {}

        self.llm = HuggingFaceInferenceAPI(
            model_name=self.llm_model,
            token=self.hf_token,
            max_input_size=2048,
            temperature=0.5,
            max_output_tokens=800,
        )
        Settings.llm = HuggingFaceInferenceAPI(
            model_name=self.llm_model,
            token=self.hf_token,
            max_input_size=2048,
            temperature=0.7,
            max_output_tokens=1024,
        )
        Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    async def handle_user_message(self, user_id):
        """Handle user message based on the mode."""
        if self.mode == 1:
            # Direct LLM response
            response = self.get_llm_response()
            return response, None
        elif self.mode in [2, 3]:
            # Check if chat engine is already set up for the user
            if user_id not in self.user_sessions:
                chat_engine, urls = await self.setup_chat_engine_with_tools()
                self.user_sessions[user_id] = chat_engine
            else:
                chat_engine = self.user_sessions[user_id]
                urls = None  # No new URLs to return

            # Use chat engine to handle the query
            response = chat_engine.chat(self.query)
            return response.response, urls


    async def save_uploaded_file(self, uploaded_file):
        """Save the uploaded file temporarily or permanently."""
        file_path = os.path.join(self.data_directory, uploaded_file.filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.file.read())
        return file_path

    async def reset_chat_memory():
        self.memory.reset()


    def get_llm_response(self):
        """Use a direct LLM for a query response."""
        client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.3", token=self.hf_token)
        messages = [{"role": "user", "content": self.query}]
        
        try:
            completion = client.chat_completion(
                messages=messages,
                max_tokens=1024,
            )
            return completion.choices[0].message["content"]
        except Exception as e:
            print(f"Failed to get LLM response: {e}")
            return "An error occurred during querying."

    # async def load_and_index_documents(self):
    #     """Automatically load all files from the given directory and create indices asynchronously."""
    #     if not os.path.exists(self.data_directory):
    #         raise FileNotFoundError(f"The directory {self.data_directory} does not exist.")
    #     # Load documents using SimpleDirectoryReader (assumed to be synchronous)
    #     reader = SimpleDirectoryReader(self.data_directory)
    #     documents = reader.load_data()
    #     # Asynchronously build indices for each document loaded
    #     async def create_index(doc):
    #         return VectorStoreIndex.from_documents([doc])
    #     indices = await asyncio.gather(*(create_index(doc) for doc in documents))

    #     # Build query engines for each index
    #     chat_engines = [index.as_query_engine() for index in indices]
    #     return chat_engines, indices

    async def load_and_index_document(self):
        """Load a single file and create an index asynchronously."""
        if not os.path.exists(self.data_directory):
            raise FileNotFoundError(f"The file {self.data_directory} does not exist.")
        # Load the document using SimpleDirectoryReader
        documents = SimpleDirectoryReader(self.data_directory).load_data()
        # Ensure there is at least one document
        if not documents:
            raise ValueError("No document found in the specified file.")
        # Create an index from the single document
        index = VectorStoreIndex.from_documents(documents)
        # Convert the index to a retriever
        retriever = index.as_retriever()
        return retriever

    async def index_web_data(self):
        """Fetch and index web data."""
        urls = self.web_search.search_web(self.query)
        indexed_urls = set()
        chat_engines = []
        chat_index = []
        for url in urls[:3]:
            if url in indexed_urls or self.web_search.is_paywalled(url):
                continue
            indexed_urls.add(url)
            try:
                # Use SimpleWebPageReader to process the HTML content of the URL
                documents = SimpleWebPageReader(html_to_text=True).load_data([url])
                if documents:
                    # Use VectorStoreIndex for indexing content after fetching the document
                    index = VectorStoreIndex.from_documents(documents)
                    chat_index.append(index)
                    chat_engine = index.as_query_engine()
                    chat_engines.append(chat_engine)
            except Exception as e:
                print(f"Failed to add URL content: {url}, Error: {e}")
        return list(indexed_urls), chat_engines, chat_index


    async def setup_chat_engine_with_tools(self):
        """Set up the chat engine with tools based on the mode."""
        urls = None
        if self.mode == 2:
            urls, chat_engines, chat_index = await self.index_web_data()
            retriever = chat_index[0].as_retriever()

            # Create QueryEngineTools for each query engine
            query_engine_tools = [
                QueryEngineTool(
                    query_engine=qe,
                    metadata=ToolMetadata(
                        name=f"query_engine_{i}",
                        description="Tool for querying indexed documents."
                    )
                )
                for i, qe in enumerate(chat_engines)
            ]
        elif self.mode == 3:
            # Mode 3 assumes a similar setup as mode 2
            retriever = await self.load_and_index_document()
            query_engine_tools = None  # No additional tools in mode

        # Conditionally include tools in the chat engine
        chat_engine = CondensePlusContextChatEngine.from_defaults(
            retriever=retriever,
            tools=query_engine_tools if self.mode == 2 else None,
            memory=self.memory,
            llm=self.llm,
            context_prompt=(
                "You are a chatbot, able to have normal interactions, as well as talk"
                " about the user's data."
                "Here are the relevant documents for the context:\n"
                "{context_str}"
                "\nInstruction: Use the previous chat history, or the context above, to interact and help the user."
            ),
            streaming=True,
            verbose=True,
        )
        return chat_engine, urls

   