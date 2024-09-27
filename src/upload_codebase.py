import fnmatch
import subprocess
import os
import json
import hashlib
from tenacity import retry, wait_random_exponential, stop_after_attempt

from configuration import Config
from open_ai_integration import OpenAIIntegration

config = Config()

def calculate_md5(input_string):
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode('utf-8'))
    return md5_hash.hexdigest()

def split_files_by_chunks(files_index, chunk_size, cwd):
    current_chunk = []
    for file_path in files_index:
        try:
            absolute_path = os.path.join(cwd, file_path)
            with open(absolute_path, 'r', encoding='utf-8') as f:
                content = f.read()
                current_chunk.append({
                    "file_path": file_path,
                    "content": content
                })
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue
        finally:
            length = len(json.dumps(current_chunk))
            if len(json.dumps(current_chunk)) > chunk_size:
                yield current_chunk
                current_chunk = []

    yield current_chunk

def get_codebase_index():
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
        cwd=config.get_target_directory_relative_path()
    )
    git_visible_files_list = result.stdout.splitlines()
    include_patterns = ['*']
    exclude_patterns = [
        '*/src/generated/*',
        '*.d.ts',
        '*.jar',
        'research/conversations/*',
        'research/README.md',
        'research/examples/*'
    ]
    matched_files_list = []
    for pattern in include_patterns:
        matched_files_list.extend([file for file in git_visible_files_list if fnmatch.fnmatch(file, pattern)])
    final_file_list = [file for file in matched_files_list if
                       not any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns)]
    file_index = sorted(final_file_list)
    return file_index

def index_codebase_content(file_index):
    chunk_size = 0.5 * 1024 * 1024  # 0.5 MB
    for chunk in split_files_by_chunks(file_index, chunk_size, config.get_target_directory_relative_path()):
        def format_file(file):
            return {
                "content": file["content"],
            }

        complete_chunk = {
            "meta": {
                "description": f"Alphabetically sorted files chunk. Presents data from codebase. Each file is a key-value pair with file_path as key and content as value.",
                "first_file": chunk[0]["file_path"],
                "last_file": chunk[-1]["file_path"],
                "files_count": len(chunk)
            },
            "files": {file["file_path"]: format_file(file) for file in chunk}
        }

        chunk_hash = calculate_md5(json.dumps(complete_chunk))

        codebase_index_chapter_name = f"{chunk_hash}.json"

        with open(codebase_index_chapter_name, 'w') as f:
            json.dump(complete_chunk, f)

        yield codebase_index_chapter_name

        os.remove(codebase_index_chapter_name)

class UploadCodebaseCommand:
    def __init__(self, client):
        self.client = client

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
    def get_codebase_store(self):
        store_id = config.vector_store_id

        try:
            store = self.client.beta.vector_stores.retrieve(store_id)
            return store
        except Exception as e:
            print(f"Error retrieving store with ID {store_id}: {e}")
            raise

    def run(self):
        store = self.get_codebase_store()
        file_index = get_codebase_index()
        chunked_codebase = index_codebase_content(file_index)
        file_streams = [open(path, "rb") for path in chunked_codebase]

        OpenAIIntegration(client=self.client).clear_files_in_store(store.id)

        self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=store.id, files=file_streams
        )


