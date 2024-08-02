import subprocess
import os


class GitDiffExtractor:
    def __init__(self, tail_commit_hash, head_commit_hash='HEAD'):
        self.tail_commit_hash = tail_commit_hash
        self.head_commit_hash = head_commit_hash

    def run(self):
        try:
            result = subprocess.run(
                ["git", "show", self.head_commit_hash, self.tail_commit_hash, "--unified=0"],
                capture_output=True,
                text=True,
                check=True,
                cwd=os.getenv('TRUNK_MONKEY_SOURCES_ROOT', '.')
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while fetching git diff: {e}")
            return []

    @staticmethod
    def get_definition():
        return {
            "name": "get_git_diff_between_commits",
            "description": "Allows to see content changes between two commits or until specific commit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tail_commit_hash": dict(type="string",
                                             description="The commit hash to be compared with HEAD."),
                    "head_commit_hash": dict(type="string",
                                             description="The commit hash to be compared with the tail_commit_hash. Default is HEAD.")
                },
                "required": [
                    "tail_commit_hash"
                ]
            }
        }
