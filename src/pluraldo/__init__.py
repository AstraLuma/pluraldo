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
@entry
async def clear():
    """
    Clears the current project
    """
    ps = await PStore.get()
    await ps.set_project(None)
    click.echo("=> cleared project")


@cli.group()
def project():
    """
    Manage projects
    """


@project.command("set")
@click.argument("project")
@entry
async def project_set(project):
    """
    Change the current project
    """
    ps = await PStore.get()
    await ps.set_project(project)
    if project:
        click.echo(f"=> working on {project}")


@project.command("ls")
@entry
async def project_ls():
    """
    List projects
    """
    ps = await PStore.get()
    async for project in ps.get_projects():
        click.echo(f"{project}")


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

    def _task_key(t):
        tid, _ = t
        proj, _, ordinal = tid.partition("-")
        return proj, int(ordinal)

    ps = await PStore.get()
    project = await ps.get_project()
    if show_all:
        project = None
    tasks = [t async for t in ps.tasks_by_title(project)]
    for tid, title in sorted(tasks, key=_task_key):
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


async def _resolve_task(ps: PStore, tid: str) -> str:
    """
    Given a potentially partial task id, resolve it to the full ID
    """
    if "-" in tid:
        # Project given, just do some normalization
        proj, _, tint = tid.partition("-")
        return f"{proj.upper()}-{tint}"
    else:
        project = await ps.get_project()
        if not project:
            raise click.UsageError("No project specified and no current project set")
        return f"{project}-{tid}"


@task.command("show")
@click.argument("task")
@entry
async def task_show(task):
    """
    Show a task, either in the current project (42) or globally (PROJ-42)
    """
    ps = await PStore.get()
    task = await _resolve_task(ps, task)
    try:
        doc = await ps.get_task(task)
    except KeyError:
        raise click.UsageError(f"Task {task} does not exist")

    # TODO: Format this nicely
    click.echo(str(doc))


@task.command("edit")
@click.argument("task")
@entry
async def task_edit(task):
    """
    Edit a task, either in the current project (42) or globally (PROJ-42)
    """
    ps = await PStore.get()
    task = await _resolve_task(ps, task)
    try:
        doc = await ps.get_task(task)
    except KeyError:
        raise click.UsageError(f"Task {task} does not exist")

    editor = TaskEditorApp(task, doc)
    await editor.run_async()

    await ps.update_task(task, doc)


@task.command("rm")
@click.argument("task")
@entry
async def task_del(task):
    """
    Delete a task, either in the current project (42) or globally (PROJ-42)
    """
    ps = await PStore.get()
    task = await _resolve_task(ps, task)
    try:
        await ps.del_task(task)
    except KeyError:
        raise click.UsageError(f"Task {task} does not exist")
    else:
        click.echo(f"=> Task {task} deleted")
