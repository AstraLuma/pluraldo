"""
Storage, but in pluraldo's terms
"""

import contextlib
import typing

import anyio
import platformdirs

from .mimestore import MimeStore, Document


class PStore:
    def __init__(self):
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
            doc = Document.from_headers(default_headers)

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
            doc["Front"] = name

    async def tasks_by_title(self) -> typing.AsyncIterator[tuple[str, str]]:
        """
        Enumerate tasks by id and title
        """
        async for id, doc in self._store.items():
            if doc["Kind"] == "task":
                yield id, doc["Title"]

    async def add_mock_task(self):
        doc = Document.from_markdown(
            "Help. Get it.", {"Kind": "task", "Title": "Get Help"}
        )
        await self._store.set("t-42", doc)

    async def get_project(self) -> str | None:
        try:
            doc = await self._store.get("_context")
            return doc["Current-Project"]
        except KeyError:
            return

    async def set_project(self, name: str):
        async with self._mutate_doc("_context", {"Kind": "context"}) as doc:
            doc["Current-Project"] = name
