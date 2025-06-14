"""
Storage, but in pluraldo's terms
"""
import typing

import anyio
import platformdirs

from .mimestore import MimeStore, Document


class PStore():
    def __init__(self):
        self._store = MimeStore(anyio.Path(platformdirs.user_data_dir("pluraldo", "Lumami")))

    @classmethod
    async def get(cls):
        self = cls()
        await self._store.root.mkdir(parents=True, exist_ok=True)
        return self

    async def get_front(self) -> str|None:
        try:
            doc = await self._store.get('_context')
        except KeyError:
            return
        else:
            return doc['Front']

    async def set_front(self, name: str):
        try:
            doc = await self._store.get('_context')
        except KeyError:
            doc = Document.from_headers(Kind='context')
        doc['Front'] = name
        await self._store.set('front', doc)

    async def tasks_by_title(self) -> typing.AsyncIterator[tuple[str, str]]:
        """
        Enumerate tasks by id and title
        """
        async for id, doc in self._store.items():
            if doc['Kind'] == 'task':
                yield id, doc['Title']
