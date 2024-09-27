import os

def get_target_directory_relative_path():
    return os.getenv('TRUNK_MONKEY_SOURCES_ROOT', '/subject')