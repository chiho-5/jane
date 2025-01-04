import os
import tempfile
from embedchain import App
from huggingface_hub import InferenceClient
from web_search import WebSearchFeature

# Set the environment variable for Hugging Face token
os.environ["HUGGINGFACE_ACCESS_TOKEN"] = "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"

class SpaceAI:
    def __init__(self, mode, query, db_path=None, llm_config=None):
        self.mode = mode
        self.query = query
        self.web_search = WebSearchFeature()
        self.db_path = db_path or tempfile.mkdtemp()

        self.llm_config = llm_config or {
            "model": "mistralai/Mistral-7B-Instruct-v0.3",
            "temperature": 0.5,
            "max_tokens": 800,
            "top_p": 0.9,
            "stream": True,
            "prompt": (
                "Use the following pieces of context to answer the query at the end.\n"
                "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"
                "$context\n\nQuery: $query\n\nHelpful Answer:"
            ),
            "model_kwargs": {"response_format": {"type": "json_object"}}
        }

        self.app = App.from_config(
            config={
                "llm": {
                    "provider": "huggingface",
                    "config": self.llm_config,
                },
                "vectordb": {
                    "provider": "chroma",
                    "config": {"collection_name": "space-ai", "dir": self.db_path, "allow_reset": True},
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {"model": "sentence-transformers/all-mpnet-base-v2"},
                },
                "chunker": {"chunk_size": 500, "chunk_overlap": 128, "length_function": "len"},
            }
        )

    def add_content_to_app(self, content):
        try:
            self.app.add(content)
        except Exception as e:
            print(f"Failed to add content: {e}")

    def index_web_data(self):
        urls = self.web_search.search_web(self.query)
        indexed_urls = set()
        for url in urls[:5]:
            if url in indexed_urls or self.web_search.is_paywalled(url):
                continue
            indexed_urls.add(url)
            try:
                self.app.add(url)
            except Exception as e:
                print(f"Failed to add URL: {url}, Error: {e}")
        return list(indexed_urls)

    def query_with_rag(self):
        try:
            return self.app.query(self.query)
        except Exception as e:
            print(f"Query failed: {e}")
            return "An error occurred during querying."

    def getLLMresponse(self):
        client = InferenceClient(api_key="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")

        messages = [
            {
                "role": "user",
                "content": self.query,
            }
        ]

        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=messages,
            max_tokens=500
        )
        return completion.choices[0].message['content']
    
    def execute_mode(self, content=None):
        """Execute actions based on the selected mode."""
        if self.mode == 1:  # Chat mode
            return self.getLLMresponse()
        elif self.mode == 2:  # Document mode
            self.index_web_data()
            return self.query_with_rag()
        elif self.mode == 3:  # Document with added content
            if content:
                self.add_content_to_app(content)
            return self.query_with_rag()
        else:
            raise ValueError("Invalid mode selected. Choose mode 1, 2, or 3.")
