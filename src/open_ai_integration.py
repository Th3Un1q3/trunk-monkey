from tenacity import retry, wait_random_exponential, stop_after_attempt

class OpenAIIntegration:
    def __init__(self, client=None):
        self.client = client

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def create_assistant(self, project_name):
        try:
            assistant = self.client.beta.assistants.create(
                    name=project_name,
                    instructions="",
                    model="gpt-4o-mini",
                )
            print(f"Created assistant with ID: {assistant.id}")
            return assistant.id
        except Exception as e:
            print(f"Error creating assistant: {e}")
            raise

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def create_vector_store(self, project_name):
        try:
            store = self.client.beta.vector_stores.create(name=project_name + " Store")
            print(f"Created vector store with ID: {store.id}")
            return store.id
        except Exception as e:
            print(f"Error creating vector store: {e}")
            raise

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def clear_files_in_store(self, vector_store_id):
        try:
            files = self.client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
            for file in files:
                self.client.beta.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file.id)
        except Exception as e:
            print(f"Error clearing files in store with ID {vector_store_id}: {e}")
            raise


    def create_resources(self, project_name):
        return {
            'assistant_id': self.create_assistant(project_name),
            'vector_store_id': self.create_vector_store(project_name),
        }