import json
from openai import AssistantEventHandler
from typing_extensions import override
from extractors.git_history import GitHistoryExtractor


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
            stream.until_done()

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
