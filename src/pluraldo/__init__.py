import functools

import anyio
import click

from .pstore import PStore


def entry(func):
    @functools.wraps(func)
    def _(*p, **kw):
        print(f"entry {func=} {p=} {kw=}")
        anyio.run(lambda: func(*p, **kw))
    return _


@click.group()
@entry
async def cli():
    pass


@cli.command()
@entry
async def whoami():
    ps = await PStore.get()
    name = await ps.get_front()
    if name is None:
        click.echo("No front")
    else:
        click.echo(f"Front: {name}")


@cli.command()
@click.argument("name")
@entry
async def switch(name):
    ps = await PStore.get()
    await ps.set_front(name)
    click.echo(f"=> switched to {name}")
