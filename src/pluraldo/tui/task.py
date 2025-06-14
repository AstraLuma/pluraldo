from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer

from ..mimestore import Document


class TaskEditor(Screen):
    def __init__(self, doc: Document):
        super().__init__()
        self.doc = doc

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


class TaskEditorApp(App):
    TITLE = "Edit Task"

    SCREENS = {}

    BINDINGS = [
        ("ctrl+q", "quit()", "Quit"),
    ]

    def __init__(self, doc: Document, **kwargs):
        super().__init__(**kwargs)
        self.doc = doc

    def on_mount(self, event):
        self.push_screen(TaskEditor(self.doc))

    def action_quit(self):
        self.exit()


if __name__ == "__main__":
    doc = Document.from_markdown("Some details", {"Kind": "task", "Title": "A task"})
    app = TaskEditorApp(doc)
    app.run()
