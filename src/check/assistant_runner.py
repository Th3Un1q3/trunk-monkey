from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from check.event_handler import MonkeyCheckEventHandler
from configuration import Config

ASSISTANT_INSTRUCTION = """# Your role

You are an observer of trunk-based development practices.

# Context


- You have access to the code base of a software project, consider searching for relevant files.
- If this benefits you can request git history, git diffs and git blame.

# Instructions

- Analyze users request, define required actions and information to perform the request.
- Specify how to better address the user's request.
- Instead of asking user if to do something proactively do so: execute functions to gather information and provide insights, look up the code.
- Explore existing code base in your filestore to provide more accurate insights.

# Communication style

- Use sarcasm, humor irony and emojis every now and then.
- Be specific and concise.
- Use code snippets and file references if necessary.
- When you are referencing something prefer to call related change contributors by their names.
"""

GPT_MODEL = "gpt-4o-mini"

class AssistantRunner:
    def __init__(self, prompt, model=None, client=None, assistant_id=None, config=None, thread_id=None):
        self.config = config or Config()
        self.prompt = prompt
        self.model = model or GPT_MODEL
        self.client = client or OpenAI(api_key=self.config.open_api_key)
        self.assistant_id = assistant_id or self.config.assistant_id
        self._thread = None
        self.thread_id = thread_id

    @property
    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def thread(self):
        if not self._thread:
            if self.thread_id:
                self._thread = self.client.beta.threads.retrieve(self.thread_id)
                print("Thread retrieved", self._thread.id)
            else:
                self._thread = self.client.beta.threads.create()
                print("Thread created", self._thread.id)
        return self._thread

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def update_assistant(self):
        def to_tool_definition(extractor):
            return {
                "type": "function",
                "function": extractor.get_definition()
            }

        tools = list(map(to_tool_definition, MonkeyCheckEventHandler.EXTRACT_TOOLS))
        tools.append({"type": "file_search"})

        tool_resources={"file_search": {"vector_store_ids": [self.config.vector_store_id]}}

        self.client.beta.assistants.update(
            assistant_id=self.assistant_id,
            instructions=ASSISTANT_INSTRUCTION,
            model=self.model,
            tools=tools,
            tool_resources=tool_resources
        )

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def send_message(self, role, content):
        return self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role=role,
            content=content
        )

    def execute(self):
        self.update_assistant()

        self.send_message(
            role="user",
            content=self.prompt
        )

        event_handler = MonkeyCheckEventHandler(client=self.client)

        with self.client.beta.threads.runs.stream(
                thread_id=self.thread.id,
                assistant_id=self.assistant_id,
                model=self.model,
                event_handler=event_handler,
        ) as stream:
            stream.until_done()

        return {
            'sandbox_url': f"https://platform.openai.com/playground/assistants?assistant={self.assistant_id}&mode=assistant&thread={self.thread.id}",
            'thread_id': self.thread.id
        }
