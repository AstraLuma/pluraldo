import functools

import anyio
import click

from .pstore import PStore


def entry(func):
    @functools.wraps(func)
    def _(*p, **kw):
        anyio.run(lambda: func(*p, **kw))

    return _


@click.group()
def cli():
    """
    Task tracking for systems
    """
    pass


@cli.command()
@entry
async def whoami():
    """
    Show the fronting alter
    """
    ps = await PStore.get()
    name = await ps.get_front()
    if name is None:
        click.echo("You are no one")
    else:
        click.echo(f"{name}")


@cli.command()
@click.argument("name")
@entry
async def switch(name):
    """
    Change the fronting alter
    """
    ps = await PStore.get()
    await ps.set_front(name)
    click.echo(f"=> switched to {name}")


@cli.group()
def task():
    """
    Manage tasks
    """
    pass


@task.command("ls")
@click.option("--all", "show_all", is_flag=True, help="Show tasks in all projects")
@entry
async def task_ls(show_all):
    """
    List tasks in the current project
    """
    ps = await PStore.get()
    async for tid, title in ps.tasks_by_title():
        click.echo(f"{tid}: {title}")


@task.command("add")
@click.argument("project", required=False)
@entry
async def task_add(project):
    """
    Interactively add a task to PROJECT or the current one
    """
    print(f"{project=}")
    ps = await PStore.get()
    await ps.add_mock_task()
