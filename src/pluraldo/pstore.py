"""
Storage, but in pluraldo's terms
"""

import contextlib
import typing
import os

import anyio
import platformdirs

from .mimestore import MimeStore, Document


class PStore:
    def __init__(self):
        # Should this use click.get_app_dir() instead?
        # https://click.palletsprojects.com/en/stable/api/#click.get_app_dir
        self._store = MimeStore(
            anyio.Path(platformdirs.user_data_dir("pluraldo", "Lumami"))
        )

    @classmethod
    async def get(cls):
        self = cls()
        await self._store.root.mkdir(parents=True, exist_ok=True)
        return self

    @contextlib.asynccontextmanager
    async def _mutate_doc(self, key, default_headers={}):
        try:
            doc = await self._store.get(key)
        except KeyError:
            doc = Document.from_headers(**default_headers)

        yield doc

        await self._store.set(key, doc)

    async def get_front(self) -> str | None:
        try:
            doc = await self._store.get("_context")
            return doc["Front"]
        except KeyError:
            return

    async def set_front(self, name: str):
        async with self._mutate_doc("_context", {"Kind": "context"}) as doc:
            del doc["Front"]
            doc["Front"] = name

    async def get_projects(self) -> typing.AsyncIterator[str]:
        """
        Enumerate projects by name
        """
        projects = set()
        async for fn in self._store.keys():
            if "-" not in fn:
                # Skip the context file
                continue
            proj, _ = fn.split("-")
            if proj not in projects:
                projects.add(proj)
                yield proj

    async def get_project(self) -> str | None:
        # Get the current project. If the environment variable
        #   `PLURALDO_PROJECT` is set, use that. Otherwise, use the currently
        #   set project.

        ## todo:
        # this is a magic string being pulled from the environment, and
        #   that is very much not ideal.
        if "PLURALDO_PROJECT" in os.environ:
            proj = os.environ["PLURALDO_PROJECT"].upper()
            return proj
        try:
            doc = await self._store.get("_context")
            proj = doc["Current-Project"]
            if proj:
                proj = proj.upper()
            return proj
        except KeyError:
            return

    async def set_project(self, name: str | None):
        async with self._mutate_doc("_context", {"Kind": "context"}) as doc:
            if name:
                del doc["Current-Project"]
                doc["Current-Project"] = name.upper()
            else:
                del doc["Current-Project"]

    async def tasks_by_title(
        self, project: str | None = None
    ) -> typing.AsyncIterator[tuple[str, str]]:
        """
        Enumerate tasks by id and title
        """
        if project:
            prefix = f"{project.upper()}-"
        else:
            prefix = ""
        async for id, doc in self._store.items():
            if doc["Kind"] == "task" and id.startswith(prefix):
                yield id, doc["Title"]

    async def get_next_id(self, project: str) -> str:
        """
        Given a project, get an unused ID within it.
        """
        project = project.upper()
        prefix = f"{project}-"
        known_ids = [
            did async for did, _ in self._store.items() if did.startswith(prefix)
        ]
        known_ints = [int(did.partition("-")[-1]) for did in known_ids]
        if known_ints:
            largest = max(known_ints)
        else:
            largest = 0
        return f"{prefix}{largest+1}"

    async def get_task(self, tid: str) -> Document:
        return await self._store.get(tid)

    async def update_task(self, tid: str, task: Document):
        assert task["Kind"] == "task"
        await self._store.set(tid, task)

    async def del_task(self, tid: str):
        await self._store.del_(tid)
