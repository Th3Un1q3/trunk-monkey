from dotenv import load_dotenv
from check.monkey_check import MonkeyCheck

load_dotenv()
load_dotenv('.env.test')
#
# MonkeyCheck(
#     check_prompt="By looking at recent commits can you tell what is the most spread and frequent struggle is?"
#     "Take into account file changes and commit messages."
#     "Also analyze affected files from attached store."
#     "Analyze at least 50 commits."
# ).execute()

# MonkeyCheck(
#     check_prompt="Analyze commits from July 5. Conclude were they:"
#     "- granular and atomic"
#     "- well documented"
#     "- change is well structured"
#     "- well tested"
# ).execute()


MonkeyCheck(
    check_prompt="# Objective"
    "Find if there are non explicit duplications between recent commits and pre-existing code."
    "Provide actionable insights and recommendations."
).execute()
