import os
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from check.event_handler import MonkeyCheckEventHandler
from extractors.git_history import GitHistoryExtractor

COMMON_INSTRUCTION = """
# Your role
You are an observer of trunk-based development practices.

# Instructions
- You have access to the code base of a software project, consider searching for relevant files.
- If this benefits you can request git history, git diffs and git blame.
- Analyze users request, define required actions and information to perform the request.
- Provide professional and weighted response, be specific and concise. Use code snippets and file references if necessary.
- Instead of asking user if to do something proactively do so: execute functions to gather information and provide insights.
- When you are referencing something prefer to call related change contributors by their names.
- Explore existing code base in your filestore to provide more accurate insights.
"""
GPT_MODEL = "gpt-4o-mini"


class MonkeyCheck:
    def __init__(self, check_prompt, model=None, client=None, assistant_id=None):
        self.check_prompt = check_prompt
        self.model = model or GPT_MODEL
        self.client = client or OpenAI()
        self.assistant_id = assistant_id or os.getenv("TRUNK_MONKEY_ASSISTANT_ID")
        self._thread = None

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def thread(self):
        if not self._thread:
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

        tool_resources={"file_search": {"vector_store_ids": [os.getenv("TRUNK_MONKEY_VECTOR_STORE_ID")]}}

        self.client.beta.assistants.update(
            assistant_id=self.assistant_id,
            instructions=COMMON_INSTRUCTION,
            model=self.model,
            tools=tools,
            tool_resources=tool_resources
        )

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def send_message(self, role, content):
        return self.client.beta.threads.messages.create(
            thread_id=self.thread().id,
            role=role,
            content=content
        )

    def execute(self):
        self.update_assistant()

        print('Open Conversation in Sandbox',
              f'https://platform.openai.com/playground/assistants?assistant={self.assistant_id}&mode=assistant&thread={self.thread().id}')

        self.send_message(
            role="user",
            content=self.check_prompt
        )

        with self.client.beta.threads.runs.stream(
                thread_id=self.thread().id,
                assistant_id=self.assistant_id,
                model=self.model,
                event_handler=MonkeyCheckEventHandler(client=self.client),
        ) as stream:
            stream.until_done()

        print("Request completed")

        print()
