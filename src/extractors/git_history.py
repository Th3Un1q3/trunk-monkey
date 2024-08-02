import json
import subprocess
import os

class GitHistoryExtractor:
    DEFAULT_NUMBER_OF_COMMITS = 20

    def __init__(self, number_of_commits):
        self.number_of_commits = number_of_commits or GitHistoryExtractor.DEFAULT_NUMBER_OF_COMMITS

    def run(self):
        try:
            result = subprocess.run(
                ["git", "log", f"-n {self.number_of_commits}", "--pretty=format:%H|%cd|%an|%s"],
                capture_output=True,
                text=True,
                check=True,
                cwd=os.getenv('TRUNK_MONKEY_SOURCES_ROOT', '.')
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

    @staticmethod
    def get_definition():
        return {
            "name": "get_git_commit_history",
            "description": "Take the history of commits, from most recent to older ones. Returns list of commits. "
                           "Allows to see at glance the history of the project, "
                           "with author name, message, date, and hash."
                           "Commit hashes can be used in other tools to fetch diffs or blame.",
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
