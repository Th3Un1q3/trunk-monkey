from typing_extensions import override
from openai import OpenAI, AssistantEventHandler
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
import os

load_dotenv()
load_dotenv('.env.test')
GPT_MODEL = "gpt-4o-mini"
ASSISTANT_ID = os.getenv("TRUNK_MONKEY_ASSISTANT_ID")
client = OpenAI()
COMMON_INSTRUCTION = """
# Your role
You are an observer of trunk-based development practices.

# Instructions
- You have access to the code base of a software project, consider searching for relevant files.
- If this benefits you can request git history, git diffs and git blame.
- Analyze users request, define required actions and information to perform the request.
- Provide professional and weighted response, be specific and concise. Use code snippets and file references if necessary.
"""

class EventHandler(AssistantEventHandler):
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


# TODO: add retry logic
def create_thread():
    thread = client.beta.threads.create()
    return thread

def execute_request(check_prompt, model=GPT_MODEL):
    check_thread = create_thread()

    print("Thread created", check_thread.id)

    print('Open Conversation in Sandbox', f'https://platform.openai.com/playground/assistants?assistant={ASSISTANT_ID}&mode=assistant&thread={check_thread.id}')

    with client.beta.threads.runs.stream(
            thread_id=check_thread.id,
            assistant_id=ASSISTANT_ID,
            model=model,
            instructions=COMMON_INSTRUCTION,
            event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

    client.beta.threads.messages.create(
        thread_id=check_thread.id,
        role="user",
        content=check_prompt
    )

def run_check():
    check_prompt = "Are you ready?"

    execute_request(check_prompt)


run_check()
