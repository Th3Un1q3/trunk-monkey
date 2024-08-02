from dotenv import load_dotenv
from check.monkey_check import MonkeyCheck

load_dotenv()
load_dotenv('.env.test')

MonkeyCheck(
    check_prompt="By looking at recent commits can you tell what is the most spread struggle is?"
    "Take into account file changes, authors, and commit messages."
    "Analyze at least 40 commits."
).execute_request()
