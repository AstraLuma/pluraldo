from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, TextArea, Label, Input, Select

from ..mimestore import Document

TASK_STATUSES = [
    ("✏️ Open", "open"),
    ("✅ Done", "done"),
]


class TaskEditor(Screen):
    CSS_PATH = "task.tcss"

    def __init__(self, taskid: str, doc: Document, **kwargs):
        super().__init__(**kwargs)
        self.taskid = taskid
        self.doc = doc

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        yield Label("Creator")
        yield (i := Input(self.doc["Creator"], id="Creator"))
        self._creator_editor = i

        yield Label("Assignee")
        yield (i := Input(self.doc["Assignee"], id="assignee"))
        self._assignee_editor = i

        yield Label("Title")
        yield (i := Input(self.doc["Title"], id="title"))
        self._title_editor = i

        yield Label("Status")
        yield (
            s := Select(
                value=self.doc["Status"],
                options=TASK_STATUSES,
                id="status",
                allow_blank=False,
            )
        )
        self._status_editor = s

        yield (
            be := TextArea.code_editor(
                str(self.doc.get_payload()),
                language="markdown",
                soft_wrap=True,
                id="body",
            )
        )
        self._body_editor = be

    async def on_unmount(self, event):
        self.doc.set_payload(self._body_editor.text)

        del self.doc["Creator"]
        self.doc["Creator"] = self._creator_editor.value

        del self.doc["Assignee"]
        self.doc["Assignee"] = self._assignee_editor.value

        del self.doc["Title"]
        self.doc["Title"] = self._title_editor.value

        del self.doc["Status"]
        self.doc["Status"] = self._status_editor.value


class TaskEditorApp(App):
    TITLE = "Edit Task"

    SCREENS = {}

    BINDINGS = [
        ("ctrl+q", "quit()", "Quit"),
    ]

    def __init__(self, taskid: str, doc: Document, **kwargs):
        self.SUB_TITLE = taskid
        super().__init__(**kwargs)
        self.taskid = taskid
        self.doc = doc

    def on_mount(self, event):
        self.push_screen(TaskEditor(self.taskid, self.doc))

    def action_quit(self):
        self.exit()


if __name__ == "__main__":
    doc = Document.from_markdown(
        "Some details",
        {
            "Kind": "task",
            "Title": "A task",
            "Creator": "Alice",
            "Assignee": "Ella",
            "Status": "open",
        },
    )
    app = TaskEditorApp("TEST-42", doc)
    app.run()
