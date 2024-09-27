import os
import yaml
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        load_dotenv('.env.test')
        self.trunk_monkey_sources_root = os.getenv('TRUNK_MONKEY_SOURCES_ROOT', '/subject')
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.manifest_path = os.path.join(self.trunk_monkey_sources_root, 'trunk_monkey_manifest.yml')
        self._assistant_id = None
        self._vector_store_id = None
        self._manifest_loaded = False

    def _load_manifest(self):
        if not self._manifest_loaded and os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'r') as file:
                manifest = yaml.safe_load(file)
                self._project_name = manifest.get('project_name')
                self._assistant_id = manifest.get('openai_config', {}).get('assistant_id')
                self._vector_store_id = manifest.get('openai_config', {}).get('vector_store_id')
            self._manifest_loaded = True

    @property
    def assistant_id(self):
        if not self._manifest_loaded:
            self._load_manifest()
        return self._assistant_id

    @property
    def vector_store_id(self):
        if not self._manifest_loaded:
            self._load_manifest()
        return self._vector_store_id

    @property
    def project_name(self):
        if not self._manifest_loaded:
            self._load_manifest()
        return self._project_name

    def get_target_directory_relative_path(self):
        return self.trunk_monkey_sources_root

    def get_api_key(self):
        return self.api_key

    def get_manifest_path(self):
        return self.manifest_path