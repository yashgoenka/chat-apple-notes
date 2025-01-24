import os
import sqlite3
import secrets
import subprocess
import hashlib
import tempfile
import typer
import sys
import time
import json
from openai import OpenAI
from typing import Dict, List, Generator, Optional

app = typer.Typer()
CONFIG_FILE = os.path.expanduser("~/chat_apple_notes_config.json")

EXTRACT_SCRIPT = """
tell application "Notes"
   repeat with eachNote in every note
      set noteId to the id of eachNote
      set noteTitle to the name of eachNote
      set noteBody to the body of eachNote
      set noteCreatedDate to the creation date of eachNote
      set noteCreated to (noteCreatedDate as «class isot» as string)
      set noteUpdatedDate to the modification date of eachNote
      set noteUpdated to (noteUpdatedDate as «class isot» as string)
      set noteContainer to container of eachNote
      set noteFolderId to the id of noteContainer
      log "{split}-id: " & noteId & "\n"
      log "{split}-created: " & noteCreated & "\n"
      log "{split}-updated: " & noteUpdated & "\n"
      log "{split}-folder: " & noteFolderId & "\n"
      log "{split}-title: " & noteTitle & "\n\n"
      log noteBody & "\n"
      log "{split}{split}" & "\n"
   end repeat
end tell
""".strip()

#error handling
class DiskAccessError(Exception):
    """Raised when disk access is required but not granted."""
    pass

class NotesAssistantConfig:
    def __init__(self) -> None:
        self.config: Dict[str, Optional[str]] = self.load_config()

    def load_config(self) -> Dict[str, Optional[str]]:
        """Load configuration from file or return default configuration."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                typer.echo("Error decoding the config file. Loading default configuration.")
        return {"assistant_id": None, "vector_store_id": None, "thread_id": None, "embedded_notes": [],
                "openai_api_key": None}

    def save_config(self) -> None:
        """Save current configuration to file."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def update_config(self, **kwargs: str) -> None:
        """Update configuration with provided key-value pairs."""
        self.config.update(kwargs)
        self.save_config()

    @property
    def assistant_id(self) -> Optional[str]:
        return self.config["assistant_id"]

    @property
    def vector_store_id(self) -> Optional[str]:
        return self.config["vector_store_id"]

    @property
    def thread_id(self) -> Optional[str]:
        return self.config["thread_id"]

    @property
    def embedded_notes(self) -> set:
        return set(self.config.get("embedded_notes", []))

    @property
    def openai_api_key(self) -> Optional[str]:
        return self.config["openai_api_key"]

    @property
    def disk_privileges(self) -> bool:
        return self.config.get("disk_privileges", False)

    def add_embedded_notes(self, note_hashes: List[str]) -> None:
        """Add new note hashes to the list of embedded notes."""
        self.config["embedded_notes"] = list(set(self.config.get("embedded_notes", []) + note_hashes))
        self.save_config()

class NotesAssistant:
    def __init__(self) -> None:
        """Initialize the NotesAssistant with configuration and OpenAI client."""
        self.config = NotesAssistantConfig()
        self.setup_api_key()
        self.setup_disk_privileges()
        self.client = OpenAI(api_key=self.config.openai_api_key)
        self.setup_assistant_and_vector_store()

    def setup_api_key(self) -> None:
        """Set up the OpenAI API key, prompting the user if necessary."""
        if not self.config.config.get("openai_api_key"):
            api_key = typer.prompt("Please enter your OpenAI API key")
            self.config.update_config(openai_api_key=api_key)
            typer.echo("API key saved. You can update it in the future by editing the config file or using update-api.")

    def setup_disk_privileges(self) -> None:
        """Prompt the user for disk privileges if not already set."""
        if "disk_privileges" not in self.config.config:
            disk_privileges = typer.confirm("Will you enabled disk privileges in OSX settings for clickable hyperlinks to your notes? (RECOMMENDED - after upload the privleges can be reverted until new notes need to be uploaded)", default=False)
            self.config.update_config(disk_privileges=disk_privileges)
            typer.echo(f"Disk privileges {'enabled' if disk_privileges else 'disabled'}. You can update it in the future by editing the config file.")

    def setup_assistant_and_vector_store(self) -> None:
        """Set up the OpenAI assistant and vector store if not already configured."""
        if not self.config.assistant_id or not self.config.vector_store_id:
            vector_store = self.client.beta.vector_stores.create(name="Apple Notes")
            assistant = self.client.beta.assistants.create(
                name="Apple Notes Assistant",
                instructions="You are an expert on the user's Apple Notes. Use your knowledge base to answer questions and provide information from the notes.",
                model="gpt-4o",
                tools=[{"type": "file_search"}],
            )
            self.client.beta.assistants.update(
                assistant_id=assistant.id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
            self.config.update_config(assistant_id=assistant.id, vector_store_id=vector_store.id)

    def get_real_identifier(self, coredata_url: str) -> Optional[str]:
        try:
            internal_db_id = coredata_url.split('/')[-1].lstrip('p')
            db_path = os.path.expanduser('~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT ZIDENTIFIER FROM ZICCLOUDSYNCINGOBJECT WHERE Z_PK=?", (internal_db_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except sqlite3.OperationalError as e:
            if "unable to open database file" in str(e):
                raise DiskAccessError("Please either grant terminal disk access privileges or use update-privileges to turn off privileges in the app.") from e
            raise

    def extract_notes(self) -> Generator[Dict[str, str], None, None]:
        """
        Extract notes from Apple Notes application.

        Yields:
            Dict[str, str]: A dictionary containing note information.
        """
        split = secrets.token_hex(8)
        process = subprocess.Popen(
            ["osascript", "-e", EXTRACT_SCRIPT.format(split=split)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        note: Dict[str, str] = {}
        body: List[str] = []

        # Get total number of notes
        total_notes = int(
            subprocess.check_output(["osascript", "-e", 'tell application "Notes" to get count of notes']).strip())

        with typer.progressbar(length=total_notes, label="Parsing notes") as progress:
            note_count = 1
            for line in process.stdout:
                line = line.decode("mac_roman").strip()
                if line == f"{split}{split}":
                    if note.get("id"):
                        note["body"] = "\n".join(body).strip()
                        note["hash"] = hashlib.sha256(f"{note['title']}{note['body']}".encode()).hexdigest()
                        if self.config.disk_privileges:
                            try:
                                note["real_id"] = self.get_real_identifier(note['id'])
                            except DiskAccessError as e:
                                typer.echo(f"\nError: {str(e)}")
                                return
                        else:
                            note["real_id"] = note['id']
                        yield note
                        note_count += 1
                        progress.update(1)
                        progress.label = f"Parsing note {note_count} of {total_notes}"
                    note, body = {}, []
                    continue
                found_key = False
                for key in ("id", "title", "folder", "created", "updated"):
                    if line.startswith(f"{split}-{key}: "):
                        note[key] = line[len(f"{split}-{key}: "):]
                        found_key = True
                        break
                if not found_key:
                    body.append(line)

    def upload(self, stop_after: Optional[int] = None) -> None:
        """
        Upload new or updated notes to the vector store.

        Args:
            stop_after (Optional[int]): If provided, stop after processing this many notes.
        """
        notes = list(self.extract_notes())[:stop_after] if stop_after else list(self.extract_notes())
        new_notes = [note for note in notes if note['hash'] not in self.config.embedded_notes]
        typer.echo(f"Extracted {len(notes)} notes. {len(new_notes)} are new or updated.")
        if not new_notes:
            typer.echo("No new or updated notes to add. Vector store is up to date.")
            return
        typer.echo("Uploading new or updated notes to vector store...")
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            for i, note in enumerate(new_notes):
                file_path = os.path.join(temp_dir, f"note_{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"Title: {note['title']}\nID: {note['real_id']}\n\nContent: {note['body']}")
                file_paths.append(file_path)
            with typer.progressbar(file_paths, label="Uploading notes") as progress:
                for i, file_path in enumerate(progress):
                    with open(file_path, 'rb') as file:
                        self.client.beta.vector_stores.file_batches.upload_and_poll(
                            vector_store_id=self.config.vector_store_id,
                            files=[file]
                        )
                    progress.label = f"Uploading note {i + 1} of {len(file_paths)}"
        self.config.add_embedded_notes([note['hash'] for note in new_notes])
        typer.echo(f"Added {len(new_notes)} new or updated notes to the vector store.")

    def search(self, query: Optional[str] = None) -> None:
        """Perform a semantic search on the notes and display results."""
        if not query:
            query = typer.prompt("Enter your search query")
        thread = self.client.beta.threads.create()
        typer.echo("Searching...")
        results = ""
        instructions = f"Search for the following query and return the top results: {query}. Start your response with I found x number of relevant notes, then newline. Do not return more than 5 results, though you can return less. For each result, return the note's title and 2 sentence description."
        if self.config.disk_privileges:
            instructions += " Also, include a link on a separate line in the format notes://showNote?identifier=id."
        with self.client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=self.config.assistant_id,
                instructions=instructions
        ) as stream:
            for event in stream:
                if event.event == 'thread.message.delta':
                    for content in event.data.delta.content:
                        if content.type == 'text':
                            results += content.text.value
                            typer.echo(content.text.value, nl=False)
                            sys.stdout.flush()
        self.client.beta.threads.delete(thread.id)
        typer.echo("\n")

    def ask(self, question: Optional[str] = None) -> None:
        """Ask a question about the notes and display the answer."""
        if not question:
            question = typer.prompt("Enter your question")
        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
        typer.echo("Answering...")
        with self.client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=self.config.assistant_id,
                instructions="Answer the user's question based on the information in their notes.",
        ) as stream:
            for event in stream:
                if event.event == 'thread.message.delta':
                    for content in event.data.delta.content:
                        if content.type == 'text':
                            typer.echo(content.text.value, nl=False)
                            sys.stdout.flush()
        self.client.beta.threads.delete(thread.id)
        typer.echo()

    def chat(self, new_chat: bool = False) -> None:
        """
        Start or continue a chat session with the assistant.

        Args:
            new_chat (bool): If True, start a new chat session. Otherwise, continue the existing one.
        """
        if new_chat or not self.config.thread_id:
            thread = self.client.beta.threads.create()
            self.config.update_config(thread_id=thread.id)
            typer.echo("Starting a new chat session.")
        else:
            typer.echo("Continuing previous chat session.")
        typer.echo("Type 'exit' to end the conversation.")
        while True:
            user_input = typer.prompt("You")
            if user_input.lower() == 'exit':
                break
            self.client.beta.threads.messages.create(thread_id=self.config.thread_id, role="user", content=user_input)
            typer.echo("Assistant: ", nl=False)
            with self.client.beta.threads.runs.stream(
                    thread_id=self.config.thread_id,
                    assistant_id=self.config.assistant_id,
                    instructions="Continue the conversation with the user.",
            ) as stream:
                for event in stream:
                    if event.event == 'thread.message.delta':
                        for content in event.data.delta.content:
                            if content.type == 'text':
                                typer.echo(content.text.value, nl=False)
                                sys.stdout.flush()
            typer.echo()

    def update_api(self, api_key: Optional[str] = None) -> None:
        """Update the OpenAI API key."""
        if not api_key:
            api_key = typer.prompt("Enter your new API key")
        self.config.update_config(openai_api_key=api_key)
        typer.echo("OpenAI API key updated.")

    def update_privileges(self, disk_privileges: Optional[bool] = None) -> None:
        """Update the disk privileges setting."""
        if disk_privileges is None:
            disk_privileges = typer.confirm("Do you want to enable disk privileges for clickable hyperlinks?")
        self.config.update_config(disk_privileges=disk_privileges)
        typer.echo(f"Disk privileges {'enabled' if disk_privileges else 'disabled'}.")

def display_welcome_animation() -> None:
    """Display a welcome animation with the Apple Notes Assistant logo."""
    logo = """
      .:'                _   _       _            
    ** :'**            | \\ | |     | |           
 .'`__`-'__``.         |  \\| | __ | |_ ___  ___ 
:__________.-'         | . ` |/ * \\| *_/ * \\/ *_|
:_________:            | |\\  | (_) | ||  **/\\** \\
 :_________`-;         |_| \\_|\\___/ \\__\\___||___/
 `.__.-.__.'
    """
    typer.echo("Welcome to Apple Notes Assistant!")
    for line in logo.split('\n'):
        typer.echo(line)
        time.sleep(0.1)

def display_main_functions() -> None:
    """Display the main functions available in the Apple Notes Assistant."""
    typer.echo("\nAvailable commands:")
    typer.echo("• upload: Extract notes and add them to the vector store")
    typer.echo("• search: Perform a semantic search on your notes")
    typer.echo("• ask: Ask a question about your notes")
    typer.echo("• chat: Start a chat session with the assistant")
    typer.echo("• update-api: Update the OpenAI API key")
    typer.echo("• update-privileges: Update disk privileges")
    typer.echo("• help: Display this help message")
    typer.echo("• quit: Exit the application")
    typer.echo("Once set up is complete you can use subcommands like chat_apple_notes search \"your query here\" or chat_apple_notes chat")

@app.command()
def interactive():
    """Start the interactive shell for the Apple Notes Assistant."""
    display_welcome_animation()
    display_main_functions()
    notes_assistant = NotesAssistant()
    typer.echo("\nStarting the interactive shell. Type 'quit' to exit the shell.")
    typer.echo("Using saved OpenAI API key. You can update it by editing the config file.")
    while True:
        command = typer.prompt("Command")
        if command.lower() == "quit":
            break
        elif command.lower() == "help":
            display_main_functions()
        else:
            process_command(command, notes_assistant)

def process_command(command: str, notes_assistant: NotesAssistant):
    try:
        if command == "upload":
            notes_assistant.upload()
        elif command.startswith("search"):
            _, *query = command.split(maxsplit=1)
            notes_assistant.search(" ".join(query) if query else None)
        elif command.startswith("ask"):
            _, *question = command.split(maxsplit=1)
            notes_assistant.ask(" ".join(question) if question else None)
        elif command == "chat":
            notes_assistant.chat()
        elif command.startswith("update-api"):
            _, *args = command.split(maxsplit=1)
            notes_assistant.update_api(args[0] if args else None)
        elif command.startswith("update-privileges"):
            _, *args = command.split(maxsplit=1)
            if args:
                dp_value = args[0].lower() in ['y', 'yes', 'true', '1']
                notes_assistant.update_privileges(dp_value)
            else:
                notes_assistant.update_privileges()
        else:
            typer.echo(f"Unknown command: {command}")
    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command()
def upload():
    """Extract notes and add them to the vector store"""
    try:
        notes_assistant = NotesAssistant()
        notes_assistant.upload()
    except Exception as e:
        typer.echo(f"Error during upload: {e}")

@app.command()
def search(query: Optional[str] = typer.Argument(None)):
    """Perform a semantic search on your notes"""
    try:
        notes_assistant = NotesAssistant()
        notes_assistant.search(query)
    except Exception as e:
        typer.echo(f"Error during search: {e}")

@app.command()
def ask(question: Optional[str] = typer.Argument(None)):
    """Ask a question about your notes"""
    try:
        notes_assistant = NotesAssistant()
        notes_assistant.ask(question)
    except Exception as e:
        typer.echo(f"Error while asking question: {e}")

@app.command()
def chat():
    """Start a chat session with the assistant"""
    try:
        notes_assistant = NotesAssistant()
        notes_assistant.chat()
    except Exception as e:
        typer.echo(f"Error during chat session: {e}")

@app.command()
def update_api(api_key: Optional[str] = typer.Argument(None)):
    """Update the OpenAI API key"""
    notes_assistant = NotesAssistant()
    notes_assistant.update_api(api_key)

@app.command()
def update_privileges(disk_privileges: Optional[bool] = typer.Argument(None)):
    """Update disk privileges"""
    notes_assistant = NotesAssistant()
    notes_assistant.update_privileges(disk_privileges)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Apple Notes Assistant - Interact with your Apple Notes using GPT"""
    if ctx.invoked_subcommand is None:
        if len(sys.argv) > 1:
            notes_assistant = NotesAssistant()
            process_command(" ".join(sys.argv[1:]), notes_assistant)
        else:
            interactive()

if __name__ == "__main__":
    app()
