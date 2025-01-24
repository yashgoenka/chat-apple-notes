# Chat Apple Notes

![License](https://img.shields.io/github/license/yashgoenka/chat-apple-notes)
![Stars](https://img.shields.io/github/stars/yashgoenka/chat-apple-notes)
![Pull Requests](https://img.shields.io/github/issues-pr/yashgoenka/chat-apple-notes)
![Issues](https://img.shields.io/github/issues/issues/yashgoenka/chat-apple-notes)

A CLI application implementing RAG (Retrieval Augmented Generation) and semantic search for Apple Notes using OpenAI's Assistants API. The tool vectorizes your notes into embeddings, enabling natural language querying through OpenAI's vector store.

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
python main.py start-shell
```

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

```bash
# Initialize vector store and upload notes
python main.py upload

# Semantic search across notes
python main.py search "query string"

# RAG-based question answering
python main.py ask "specific question"

# Interactive chat session with context
python main.py chat
```

## Implementation Details

- Uses AppleScript for native Notes.app interaction
- Implements SHA-256 content hashing for change detection
- Leverages OpenAI's Assistant API with GPT-4 for RAG capabilities
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