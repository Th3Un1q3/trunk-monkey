from distutils.sysconfig import project_base

import click

from check.check_definition import CheckDefinition
from check.assistant_runner import AssistantRunner
from configuration import Config
from open_ai_integration import OpenAIIntegration
from upload_codebase import UploadCodebaseCommand
import yaml
import os
from openai import OpenAI

config = Config()


@click.group()
def cli():
    pass


@click.command()
@click.option('--project_name', prompt='Project Name', help='Name to be used to address the project.')
def init(project_name):
    """Sets up manifest file for the project. Initiates assistant and vector store"""
    # throw error if manifest file already exists
    if os.path.exists(config.manifest_path):
        click.echo('Manifest file already exists. Exiting...')
        return

    click.echo('Initializing trunk monkey assistant instance...')
    click.echo('Initializing vector store...')

    manifest_content = {
        'manifest_version': '1.0',
        'project_name': project_name,
        'openai_config': OpenAIIntegration(client=OpenAI(
            api_key=config.open_api_key
        )).create_resources(project_name),
        'source_files': {
            'include': ['*'],
            "exclude": []
        }
    }

    click.echo('Creating manifest file...')
    with open(config.manifest_path, 'w') as file:
        yaml.dump(manifest_content, file, default_flow_style=False)

    click.echo('Initialization complete!')


@click.command()
def sync():
    """Upload the project's codebase to the vector store"""
    click.echo('Syncing project with the latest changes...')
    click.echo('Uploading code...')
    UploadCodebaseCommand(
        client=OpenAI(api_key=config.open_api_key)
    ).run()
    click.echo('Upload complete!')
    click.echo('Synchronization complete!')


@click.command()
def check_all():
    """Checks the project for code smells, anti-patterns, and duplicates"""
    click.echo('Checking project for code smells, anti-patterns, and duplicates...')

    checks = [
        # CheckDefinition(
        #     check_id="deduplication",
        #     prompt="Check what was added/changed in the last commit."
        #            "Using file search look if this change introduces duplication with existing code."
        #            "Also check if there were missed opportunities to reuse existing code."
        #            "Provide actionable insights and recommendations."
        # ),
        # CheckDefinition(
        #     check_id="struggle",
        #     prompt="By looking at recent commits can you tell what is the most spread and frequent struggle is?"
        #            "Take into account file changes and commit messages."
        #            "Also analyze affected files from attached store."
        #            "Analyze at least 30 commits."
        # ),
        # CheckDefinition(
        #     check_id="trunk_based_dev",
        #     prompt="""Review recent commits log and code.
        #            Conclude if commits follow trunk based development best practices and implement following properties:
        #            - granular and atomic, and isolated
        #            - well documented
        #            - change is well structured
        #            - well tested
        #            """
        # ),
        CheckDefinition(
            check_id="documentation_integrity",
            prompt="Review changes from the last commit."
                   "Find what documentation is not reflecting what was changed by the commit."
        ),
    ]

    thread_id = None

    for check in checks:
        result = AssistantRunner(
            prompt=check.prompt,
            thread_id=thread_id,
        ).execute()
        if not thread_id:
            thread_id = result['thread_id']
        click.echo(f'Check complete: {check.check_id}')
        click.echo("View in sandbox: " + result['sandbox_url'])


cli.add_command(init)
cli.add_command(sync)
cli.add_command(check_all)

if __name__ == '__main__':
    cli()
