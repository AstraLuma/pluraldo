import functools

import anyio
import click

from .pstore import PStore
from .mimestore import Document

from .tui.task import TaskEditorApp


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


@cli.command()
@click.argument("project", required=False)
@entry
async def workon(project):
    """
    Change the current project, or unset it
    """
    if project:
        project = project.upper()
    ps = await PStore.get()
    await ps.set_project(project)
    if project:
        click.echo(f"=> working on {project}")
    else:
        click.echo("=> cleared project")


@cli.group()
def task():
    """
    Manage tasks
    """


@task.command("ls")
@click.option("--all", "show_all", is_flag=True, help="Show tasks in all projects")
@entry
async def task_ls(show_all):
    """
    List tasks in the current project
    """
    ps = await PStore.get()
    project = await ps.get_project()
    if show_all:
        project = None
    async for tid, title in ps.tasks_by_title(project):
        click.echo(f"{tid}: {title}")


@task.command("add")
@click.argument("project", required=False)
@entry
async def task_add(project):
    """
    Interactively add a task to PROJECT or the current one
    """
    ps = await PStore.get()
    if not project:
        project = await ps.get_project()
    if not project:
        raise click.UsageError("No project specified and no current project set")
    project = project.upper()
    alter = await ps.get_front()

    tid = await ps.get_next_id(project)
    task = Document.from_markdown(
        "", {"Kind": "task", "Title": "", "Creator": alter or "", "Assignee": ""}
    )

    editor = TaskEditorApp(tid, task)
    await editor.run_async()

    if task["Title"] or task.get_payload():
        await ps.update_task(tid, task)


@task.command("show")
@click.argument("task")
@entry
async def task_show(task):
    """
    Show a task, either in the current project (42) or globally (PROJ-42)
    """
    ps = await PStore.get()
    if "-" not in task:
        project = await ps.get_project()
        if not project:
            raise click.UsageError("No project specified and no current project set")
        task = f"{project}-{task}"
    try:
        doc = await ps.get_task(task)
    except KeyError:
        raise click.UsageError(f"Task {task} does not exist")

    # TODO: Format this nicely
    click.echo(str(doc))
