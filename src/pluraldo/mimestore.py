"""
A key/document store using MIMEish messages as the documents
"""

import email.charset
import email.message
import email.parser
import email.policy
import typing

import anyio


_StorePolicy = email.policy.default.clone(
    linesep="\r\n", max_line_length=None, utf8=True
)


class _StoreCharset(email.charset.Charset):
    output_charset = "utf-8"

    def __init__(self):
        pass

    def __repr__(self):
        return "_StoreCharset()"

    def get_body_encoding(self):
        return lambda msg: None

    def get_output_charset(self):
        return "utf-8"

    def header_encode(self, string):
        return string

    def header_encode_lines(self, string, maxlengths):
        return [string]

    def body_encode(self, string):
        return string


class Document(email.message.Message):
    def __init__(self):
        super().__init__(_StorePolicy)

    def __setitem__(self, name, val):
        if name.lower() == "mime-version":
            return
        else:
            super().__setitem__(name, val)

    def set_payload(self, payload):
        if isinstance(payload, str):
            super().set_payload(payload, _StoreCharset())
        else:
            super().set_payload(payload)

    @classmethod
    def from_markdown(
        cls, body: str, headers: dict[str, str] | None = None
    ) -> typing.Self:
        self = cls()
        self.set_payload(body)
        self.set_type("text/markdown")
        if headers:
            for key, value in headers.items():
                self[key] = value
        return self

    @classmethod
    def from_headers(cls, **headers) -> typing.Self:
        self = cls()
        for key, value in headers.items():
            self[key] = value
        return self

    @classmethod
    def from_bytes(cls, message: bytes) -> typing.Self:
        p = email.parser.BytesParser(cls, policy=_StorePolicy)
        return p.parsebytes(message)


# Characters that can't appear in the name, mostly Windows
RESERVED_CHARS = '<>:"/\\|?*'
_RC_TABLE = str.maketrans("", "", RESERVED_CHARS)

# Illegal basenames, mostly Windows. The superscripts are not a mistake.
RESERVED_BASES = [
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "COM¹",
    "COM²",
    "COM³",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
    "LPT¹",
    "LPT²",
    "LPT³",
]


def _is_legal(file: anyio.Path) -> bool:
    """
    Checks that a filename is legal on all systems. Does not check parents.

    This exists so that pluraldo's data can be synchronized between systems
    """
    if file.name.translate(_RC_TABLE) != file.name:
        return False
    if file.stem in RESERVED_BASES:
        return False
    return True


class MimeStore:
    def __init__(self, root: anyio.Path):
        self.root = root

    def __repr__(self):
        return f"{type(self).__name__}({self.root!r})"

    async def keys(self) -> typing.AsyncIterator[str]:
        async for f in self.root.iterdir():
            yield f.name

    async def items(self) -> typing.AsyncIterator[tuple[str, Document]]:
        async for f in self.root.iterdir():
            payload = await f.read_bytes()
            yield f.name, Document.from_bytes(payload)

    async def values(self) -> typing.AsyncIterator[Document]:
        async for _, v in self.items():
            yield v

    def _file(self, key: str) -> anyio.Path:
        assert "/" not in key
        f = self.root / key
        if not _is_legal(f):
            raise ValueError(f"{key!r} isn't a valid filename on all systems")
        return f

    async def get(self, key: str) -> Document:
        try:
            payload = await self._file(key).read_bytes()
        except FileNotFoundError as exc:
            raise KeyError(f"Key {key!r} not found") from exc
        return Document.from_bytes(payload)

    async def set(self, key: str, value: Document):
        payload = bytes(value)
        await self._file(key).write_bytes(payload)

    async def del_(self, key: str):
        await self._file(key).unlink()
