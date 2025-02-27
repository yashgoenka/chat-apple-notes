# Chat Apple Notes

![License](https://img.shields.io/github/license/yashgoenka/chat-apple-notes)
![Pull Requests](https://img.shields.io/github/issues-pr/yashgoenka/chat-apple-notes)
![Issues](https://img.shields.io/github/issues/yashgoenka/chat-apple-notes)
[![Twitter Follow](https://img.shields.io/twitter/follow/theyashgoenka?style=social)](https://twitter.com/theyashgoenka)
![Stars](https://img.shields.io/github/stars/yashgoenka/chat-apple-notes)


A CLI application implementing RAG (Retrieval Augmented Generation) and semantic search for Apple Notes using OpenAI's Assistants API. The tool vectorizes your notes into embeddings, enabling natural language querying through OpenAI's vector store.

https://github.com/user-attachments/assets/3f62b195-d580-46cb-bc9b-4563a6023839

*Demo: Chat Apple Notes in action*

## Key Features

- **Vector Store Integration**: Extracts Apple Notes via AppleScript and creates embeddings using OpenAI's vector store
- **Semantic Search**: Queries note embeddings to find contextually relevant matches
- **RAG-based Queries**: Leverages note embeddings for context-aware question answering
- **Conversational Interface**: Maintains chat context through OpenAI's thread management

## Installation

Requirements:
- Python 3.7+
- macOS (for Apple Notes access)
- OpenAI API key

```bash
# Clone repository
git clone https://github.com/yashgoenka/chat-apple-notes
cd chat-apple-notes

# Install dependencies
pip install -r requirements.txt

# Launch CLI
python chat_apple_notes.py
```

## Getting Started

The recommended way to begin is by entering the CLI interface:

```bash
python chat_apple_notes.py
#greeted with welcome message and instructions
#enter api key
Command: upload
#Parsing note 1142 of 1142  [####################################]  100%          
#Extracted 1142 notes. 1142 are new or updated.
#Uploading new or updated notes to vector store...
#Uploading note 1142 of 1142  [####################################]  100%          
#Added 1142 new or updated notes to the vector store.
Command: search
#Enter your search query:
#semantic search results 
Command: search "query string"
#semantic search results
Command: ask
#Enter your question: what's phonecall.bot?
#Answering...
#Phonecall.bot is an AI-powered phone automation service by Orange AI Inc. that creates hyper-realistic AI phone agents. It allows businesses to automate both inbound and outbound calls using advanced conversational AI technology. Some key features include hyper-realistic voice options, multilingual support, automated appointment booking, human transfer capability, and knowledge integration for contextual awareness. The platform offers 60+ unique voices in 15+ languages and includes a no-code AI agent builder with custom conversation paths. It integrates with calendars, CRMs, and other tools, aiming to streamline operations, enhance customer support, and scale communication without the need for human agents【4:0†note_30.txt】.
Command: ask "Write a welcome email for Tom from Molar Bear Dentistry explaining them phonecall.bot features"
#Answering...
#Certainly! Here's a draft for a welcome email to Molar Bear Dentistry, introducing them to the features of Phonecall.bot:
#---
#Subject: Welcome to the Future of Patient Communication with Phonecall.bot
#Hey Tom,
#We are thrilled to welcome  Molar Bear Dentistry to the Phonecall.bot family! We are committed to enhancing your communication capabilities, allowing you to focus more on what you do best—providing exceptional dental care to your patients.
#
#**Explore What Phonecall.bot Can Do for You:**
#- **AI-Powered Agents:** Our platform offers hyper-realistic,...
Command: chat
#Continuing previous chat session.
#Type 'exit' to end the conversation.
#You: Do you know who I am? My name?
#Assistant: Based on the information from the documents, your name is Yash, and you are associated with the company Phonecall.bot【22:0†source】.
#You: What hobbies do I like to do?
#Assistant: Based on the documents, your hobbies include playing tennis, golf, grabbing drinks with friends, and occasionally oil painting【26:0†file-YMae4u6E2SSWv8kz2WZYib】【26:3†file-8VmDeabvm89A3gGXtWe7i8】. Additionally, you have interests in painting/drawing, going to the beach, traveling, and surfing【26:8†file-Ns9uJ7awM4FdNuPJapaAta】.
#You: What supplements do I take?
#Assistant: The list of supplements you take includes:
#- Vitamin D3
#- Vitamin B12
#- DHA, Omega 3, Omega 6
#- Life Extension Multivitamin
#You: 
```

Alternatively, you can execute commands directly from the terminal:

```bash
# Semantic search across notes
python chat_apple_notes.py search "query string"

# RAG-based question answering
python chat_apple_notes.py ask "specific question"

# Interactive chat session with context
python chat_apple_notes.py chat
```

## Note: The initial upload process occurs in two phases:

1. **Note Extraction & Parsing** (5-15 minutes)
   - AppleScript extracts all notes and metadata
   - Content is parsed and hashed locally
   - Progress bar shows notes processed

2. **Vectorization & Upload** (10 minutes - 2 hours)
   - Notes are batched for embedding generation
   - Vectors uploaded to OpenAI's store
   - Rate limited by OpenAI's API quotas
   - Progress bar shows upload status

The duration depends on:
- Total number of notes
- Average note length
- OpenAI API rate limits
- System performance

This is a one-time setup process. Subsequent uploads/updates will only process new or modified notes based on content hashing.

## Command Reference

### `upload`
Extracts notes via AppleScript, vectorizes content, and uploads to OpenAI's vector store. Tracks changes through content hashing to avoid duplicate uploads.

### `search <query>`
Performs semantic search across vectorized notes using cosine similarity. Returns contextually relevant matches with clickable note links (requires disk access privileges).

### `ask <question>`
Executes RAG using the vector store as context to generate answers grounded in your notes' content.

### `chat`
Initiates a stateful conversation, maintaining context through OpenAI's thread management. The assistant references relevant notes during the conversation.

### `update-api`
Updates stored OpenAI API key.

### `update-privileges`
Toggles disk access for clickable note links. Required for initial upload and hyperlink functionality.

## Implementation Details

- Uses AppleScript for native Notes.app interaction
- Implements SHA-256 content hashing for change detection
- Leverages OpenAI's Assistant API with GPT-4o for RAG capabilities
- Manages conversation state through OpenAI's thread system
- SQLite integration for note identifier resolution

## Technical Architecture

```
AppleScript Extraction -> SQLite ID Mapping -> Vector Store Embedding -> GPT-4o Assistant
```

1. **Note Extraction**: 
   - Uses AppleScript to batch extract notes including metadata
   - Maps internal CoreData IDs to external identifiers via SQLite queries
   - Maintains content hash registry to track changes

2. **Vector Store Integration**:
   - Embeds note content using OpenAI's text-embedding model
   - Stores embeddings in OpenAI's Vector Store for efficient similarity search
   - Implements incremental updates based on content hashing

3. **Query Processing**:
   - Performs semantic search using embedded vectors
   - Retrieves relevant note segments as context
   - Augments GPT-4o prompts with retrieved context

## Privacy Considerations

- Notes are processed locally before vectorization
- Content is sent to OpenAI for embedding generation and RAG
- API keys stored locally in `~/chat_apple_notes_config.json`
- Optional disk access required for hyperlink functionality

## Terminal Disk Access Setup

You'll need to grant Full Disk Access to Terminal (or your preferred terminal emulator) in macOS System Settings. This is required for the note hyperlink functionality.

1. Open System Settings
2. Navigate to Privacy & Security > Full Disk Access
3. Ensure the toggle next to Terminal is enabled

<img src="docs/terminal_disk_access.png" width="600" alt="Terminal Full Disk Access Settings"/>

## Limitations

- Requires macOS and Apple Notes.app
- Terminal needs disk access for note hyperlinking
- Rate limited by OpenAI API quotas
- Limited to text content (no media handling)

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Disclaimer

Independent project, not affiliated with Apple or OpenAI. Use within Apple's & OpenAI's terms of service.
