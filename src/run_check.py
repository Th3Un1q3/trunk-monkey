from dotenv import load_dotenv
from monkey_check import MonkeyCheck

load_dotenv()
load_dotenv('.env.test')

MonkeyCheck(
    check_prompt="How frequently should I commit to trunk? And how would you characterize our commit frequency, review larger timeframe?"
).execute_request()
