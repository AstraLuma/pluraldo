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


STATUS_ICONS = {
    ...: "❓",
    "open": "✏️",
    "done": "✅",
    "blocked": "🛑",
}


@task.command("ls")
@click.option("--all", "show_all", is_flag=True, help="Show tasks in all projects")
@click.option("--done", "show_done", is_flag=True, help="Show finished tasks")
@entry
async def task_ls(show_all, show_done):
    """
    List tasks in the current project
    """

    def _task_key(t):
        tid, _ = t
        proj, _, ordinal = tid.partition("-")
        return proj, int(ordinal)

    ps = await PStore.get()
    project = await ps.get_project()
    prefix = f"{project.upper()}-"
    match (show_all, show_done):
        case (False, False):

            def pred(k, d):
                return k.startswith(prefix) and d["Status"] != "done"
        case (False, True):

            def pred(k, d):
                return k.startswith(prefix)
        case (True, False):

            def pred(k, d):
                return d["Status"] != "done"
        case (True, True):

            def pred(k, d):
                return True

    tasks = [t async for t in ps.task_search(pred)]
    for tid, task in sorted(tasks, key=_task_key):
        if task["Status"]:
            icon = STATUS_ICONS.get(task["Status"].lower(), STATUS_ICONS[...])
        else:
            icon = STATUS_ICONS[...]
        click.echo(f"{tid}{icon}: {task['Title']}")


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
    # FIXME: Reserve this ID
    task = Document.from_markdown(
        "",
        {
            "Kind": "task",
            "Title": "",
            "Creator": alter or "",
            "Assignee": "",
            "Status": "open",
        },
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
        async with ps.mutate_task(task, must_exist=True) as doc:
            editor = TaskEditorApp(task, doc)
            await editor.run_async()
    except KeyError:
        raise click.UsageError(f"Task {task} does not exist")


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


@task.command("start")
@click.argument("task")
@entry
async def task_start(task):
    """
    Start a task, either in the current project (42) or globally (PROJ-42). Also
    updates the assignee.
    """
    ps = await PStore.get()
    task = await _resolve_task(ps, task)
    alter = await ps.get_front()
    try:
        async with ps.mutate_task(task, must_exist=True) as doc:
            del doc["Assignee"]
            doc["Assignee"] = alter

            del doc["Status"]
            doc["Status"] = "open"
    except KeyError:
        raise click.UsageError(f"Task {task} does not exist")
    else:
        click.echo(f"=> Task {task} ({doc['Title']}) marked as started")


@task.command("done")
@click.argument("task", required=False)
@click.option("--take", "take", is_flag=True, help="Also set the assignee")
@entry
async def task_done(task, take):
    """
    Finish a task, either in the current project (42) or globally (PROJ-42).
    """
    ps = await PStore.get()
    task = await _resolve_task(ps, task)
    alter = await ps.get_front()
    try:
        async with ps.mutate_task(task, must_exist=True) as doc:
            del doc["Status"]
            doc["Status"] = "done"
            if take:
                del doc["Assignee"]
                doc["Assignee"] = alter

            del doc["Status"]
            doc["Status"] = "done"
    except KeyError:
        raise click.UsageError(f"Task {task} does not exist")
    else:
        click.echo(f"=> Task {task} ({doc['Title']}) marked as done")
