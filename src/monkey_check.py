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
    def __init__(self, number_of_commits):
        self.number_of_commits = number_of_commits

    @staticmethod
    def get_definition():
        return {
            "name": "get_git_commit_history",
            "description": "Take the history of commits, from most recent to older ones. Returns list of commits, with author name, message, date, and hash.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number_of_commits": {
                        "type": "number",
                        "description": "Number of commits to be fetched. Default is 10."
                    }
                },
                "required": [
                    "number_of_commits"
                ]
            }
        }

    def run(self):
        return """
4aa8c5322d18d846f12c799a671432dd8aae51a9|Tue Jul 23 19:06|john.doe|add requesting function and dev environment
f80d69fb8b04225e77142267cb5ec17099d81e51|Tue Jul 23 16:04|john.doe|add scaffold for function based queries
d2bd172e40d2e1f9c437ed4ddccf257e666c6e14|Mon Jul 22 13:26|john.doe|Add one more check
162fac30a0588602ce6759a204e3b07deec0798f|Fri Jul 19 18:17|john.doe|preserve conversation
09c3dae75f30064d4adedec738531c3a346f0568|Fri Jul 19 18:17|john.doe|experiment with bigger contexts
9a09f7ce9d5f8748ff309a6bb6c0eaa418b7dad6|Fri Jul 19 15:31|john.doe|add more context gathering tasks
10400479c73d2bf76ada54efa6c9ed6b25329b82|Fri Jul 19 13:54|john.doe|save sample of a diff output
d6251eacc556f658a787a4f7ae864a94c9e6dc14|Fri Jul 19 13:46|john.doe|complete extended experiment
4b01a93c4c3a520e275baac035fac2b147f30481|Fri Jul 19 13:14|john.doe|complete first experiment
7182b91fbfb5a0d705d98b805be4963f655f315e|Fri Jul 19 13:03|john.doe|add sandbox and research design
491a70636aa69e24c3d5b6586400ac2b1f72aa97|Fri Jul 19 11:42|john.doe|add duplicate example to experiments
b63e2f689a6ae5dd54794348a3f3d42732468479|Fri Jul 19 10:22|john.doe|docs: refine context definition experiment
94f278b834c9f88dff8d46fbd187828132316a07|Fri Jul 19 09:22|john.doe|docs: design experiments
0cde3e1c76db6ea84a0c6ef4f7ff5cab1a7484c2|Wed Jul 17 16:42|John Doe|docs: better text in checks
2e4a45ab8d3b537fd6ea12b20abffb75f9bcc277|Wed Jul 17 16:42|John Doe|docs: add monkey checks
e3de96cea4429867aa4247d259e094c279c418bd|Sat Jul 6 12:17|John Doe|add purpose to readme.md
bbd2f2f0635d01fad503e5327d1d0e63ef28c671|Fri Jul 5 19:31|John Doe|Initial commit
        """

        # try:
        #     result = subprocess.run(
        #         ["git", "log", f"-n {self.number_of_commits}", "--pretty=format:%H|%ct|%ah|%s"],
        #         capture_output=True,
        #         text=True,
        #         check=True
        #     )
        #     commits = []
        #     for line in result.stdout.splitlines():
        #         commit_hash, timestamp, author, message = line.split('|', 3)
        #         commits.append({
        #             "commit_hash": commit_hash,
        #             "timestamp": timestamp,
        #             "author": author,
        #             "message": message
        #         })
        #     return commits
        # except subprocess.CalledProcessError as e:
        #     print(f"An error occurred while fetching git history: {e}")
        #     return []


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
