# Schema
Since pluraldo uses a schemaless store, the schema needs to be tracked informally.

Documents have an ID, headers, and a body. Multiple copies of the same header may be present. It is assumed that documents associated with a project (eg Tasks) will have IDs in the form of PROJ-123

## Context
This is only for the `_context` document.

* `Kind` (string): `"context"`
* `Front` (string, missing): The current alter, as a username
* `Current-Project` (string, missing): The current project, as an all caps prefix.

The body is empty.


## Task
A thing to do

* `Kind` (string): `"task"`
* Project is in the document key
* `Title` (string): Short description of the task
* `Creator` (string): The alter that created the task, as a username
* `Assignee` (string): The alter that's currently working on the task as a username, or empty string
* `Status` (string): One of `"open"`, `"done"`, `"blocked"`

The body is markdown, containing the full description.

Task status icons: ❓, ✏️, ✅, 🛑


## Alter

Alter is an implied object with only a string username.


## Project

Project is an implied object with only a string project prefix.
