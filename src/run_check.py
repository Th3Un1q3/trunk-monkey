from dotenv import load_dotenv
from check.monkey_check import MonkeyCheck

load_dotenv()
load_dotenv('.env.test')

MonkeyCheck(
    check_prompt="By looking at recent commits can you tell what is the most spread struggle is?"
).execute_request()
