import os
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt

class OpenAIIntegration:
    def __init__(self, client=None):
        self.client = client

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def create_assistant(self):
        try:
            assistant = self.client.beta.assistants.create(
                    name="Trunk Monkey V1",
                    instructions="",
                    model="gpt-4o-mini",
                )
            print(f"Created assistant with ID: {assistant.id}")
            return assistant.id
        except Exception as e:
            print(f"Error creating assistant: {e}")
            raise

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def create_vector_store(self):
        try:
            store = self.client.beta.vector_stores.create(name="trunk-monkey-codebase_v1")
            print(f"Created vector store with ID: {store.id}")
            return store.id
        except Exception as e:
            print(f"Error creating vector store: {e}")
            raise

    def create_resources(self):
        return {
            'assistant_id': self.create_assistant(),
            'vector_store_id': self.create_vector_store(),
        }