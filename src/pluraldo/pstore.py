"""
Storage, but in pluraldo's terms
"""
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
            doc = await self._store.get('front')
        except KeyError:
            return
        else:
            return doc['Name']

    async def set_front(self, name: str):
        doc = Document.from_headers(Species='front', Name=name)
        await self._store.set('front', doc)