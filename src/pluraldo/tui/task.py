from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, TextArea

from ..mimestore import Document


class TaskEditor(Screen):
    def __init__(self, taskid: str, doc: Document, **kwargs):
        super().__init__(**kwargs)
        self.taskid = taskid
        self.doc = doc

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        yield (
            be := TextArea.code_editor(
                self.doc.get_payload(), language="markdown", soft_wrap=True, id="body"
            )
        )
        self._body_editor = be

    async def on_unmount(self, event):
        self.doc.set_payload(self._body_editor.text)


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
    doc = Document.from_markdown("Some details", {"Kind": "task", "Title": "A task"})
    app = TaskEditorApp("TEST-42", doc)
    app.run()
