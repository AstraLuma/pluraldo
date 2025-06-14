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
    pass


@cli.command()
@entry
async def whoami():
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
    ps = await PStore.get()
    await ps.set_front(name)
    click.echo(f"=> switched to {name}")


@cli.group()
def task():
    pass


@task.command("ls")
@entry
async def task_ls():
    ps = await PStore.get()
    async for tid, title in ps.tasks_by_title():
        click.echo(f"{tid}: {title}")


@task.command("add")
@entry
async def task_add():
    ps = await PStore.get()
    await ps.add_mock_task()
