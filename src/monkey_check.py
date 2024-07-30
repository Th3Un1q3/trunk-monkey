import json
from typing_extensions import override
from openai import OpenAI, AssistantEventHandler
from tenacity import retry, wait_random_exponential, stop_after_attempt
import os
import subprocess

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
"""
GPT_MODEL = "gpt-4o-mini"


class GitHistoryExtractor:
    DEFAULT_NUMBER_OF_COMMITS = 20

    def __init__(self, number_of_commits):
        self.number_of_commits = number_of_commits or DEFAULT_NUMBER_OF_COMMITS

    @staticmethod
    def get_definition():
        return {
            "name": "get_git_commit_history",
            "description": "Take the history of commits, from most recent to older ones. Returns list of commits, "
                           "with author name, message, date, and hash.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number_of_commits": dict(type="number",
                                              description=f"Number of commits to be fetched. Default is {GitHistoryExtractor.DEFAULT_NUMBER_OF_COMMITS}.")
                },
                "required": [
                    "number_of_commits"
                ]
            }
        }

    def run(self):
        try:
            result = subprocess.run(
                ["git", "log", f"-n {self.number_of_commits}", "--pretty=format:%H|%cd|%an|%s"],
                capture_output=True,
                text=True,
                check=True,
                cwd='/subject'
            )

            commits = []
            for line in result.stdout.splitlines():
                commit_hash, timestamp, author, message = line.split('|', 3)
                commits.append({
                    "commit_hash": commit_hash,
                    "timestamp": timestamp,
                    "author": author,
                    "message": message
                })
            return json.dumps(commits)
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while fetching git history: {e}")
            return []


class MonkeyCheckEventHandler(AssistantEventHandler):
    def __init__(self, client):
        super().__init__()
        self.client = client

    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data, run_id):
        tool_outputs = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == GitHistoryExtractor.get_definition().get("name"):
                print(f"Fetching git history with {tool.function.arguments} commits")

                number_of_commits = json.loads(tool.function.arguments)["number_of_commits"]
                git_history_extractor = GitHistoryExtractor(number_of_commits)
                git_history = git_history_extractor.run()
                tool_outputs.append({"tool_call_id": tool.id, "output": git_history})

        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with self.client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=self.current_run.thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                event_handler=MonkeyCheckEventHandler(self.client),
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
            print()

    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)


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
        self.client.beta.assistants.update(
            assistant_id=self.assistant_id,
            instructions=COMMON_INSTRUCTION,
            model=self.model,
            tools=[
                {
                    "type": "function",
                    "function": GitHistoryExtractor.get_definition()
                }
            ]
        )

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def send_message(self, role, content):
        return self.client.beta.threads.messages.create(
            thread_id=self.thread().id,
            role=role,
            content=content
        )

    def execute_request(self):
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
