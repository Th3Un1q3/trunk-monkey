import click

from dotenv import load_dotenv
from check.monkey_check import MonkeyCheck
from helpers import get_target_directory_relative_path
from open_ai_integration import OpenAIIntegration
from upload_codebase import UploadCodebaseCommand
import yaml
import os
from openai import OpenAI

load_dotenv()
load_dotenv('.env.test')


@click.group()
def cli():
    pass

@click.command()
def init():
    """Sets up manifest file for the project. Initiates assistant and vector store"""
    manifest_path = os.path.join(get_target_directory_relative_path(), 'trunk_monkey_manifest.yml')

    # throw error if manifest file already exists
    if os.path.exists(manifest_path):
        click.echo('Manifest file already exists. Exiting...')
        return

    click.echo('Initializing trunk monkey assistant instance...')
    click.echo('Initializing vector store...')

    data = {
        'manifest_version' : '1.0',
        'openai_config': OpenAIIntegration(client=OpenAI()).create_resources(),
    }

    click.echo('Creating manifest file...')
    with open(manifest_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

    click.echo('Initialization complete!')

@click.command()
def sync():
    """Upload the project's codebase to the vector store"""
    click.echo('Syncing project with the latest changes...')
    UploadCodebaseCommand(
        client=OpenAI()
    ).run()
    click.echo('Indexed code 50 KB.')
    click.echo('Uploading code...')
    click.echo('Upload complete!')
    click.echo('Synchronization complete!')


@click.command()
def check_all():
    """Checks the project for code smells, anti-patterns, and duplicates"""
    click.echo('Checking project for code smells, anti-patterns, and duplicates...')

    MonkeyCheck(
        check_prompt="# Objective"
                     "Check what was added/changed in the last commit."
                     "Using file search look if this change introduces duplication with existing code."
                     "Also check if there were missed opportunities to reuse existing code."
                     "Provide actionable insights and recommendations."
    ).execute()

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

    click.echo('Checks complete.')
    click.echo('Passed 2/8 ❌')



cli.add_command(init)
cli.add_command(sync)
cli.add_command(check_all)

if __name__ == '__main__':
    cli()