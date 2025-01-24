# Chat Apple Notes
![License](https://img.shields.io/github/license/yashgoenka/chat-apple-notes)
![Stars](https://img.shields.io/github/stars/yashgoenka/chat-apple-notes)
![Pull Requests](https://img.shields.io/github/issues-pr/yashgoenka/chat-apple-notes)
![Issues](https://img.shields.io/github/issues/yashgoenka/chat-apple-notes)

RAG + Semantic Search for Apple Notes on CLI

Chat Apple Notes is a CLI application that allows users to interact with their Apple Notes using GPT-powered AI. This tool enables users to search, query, and chat about their notes in natural language, providing a deeper and more intuitive way to engage with their personal information.

## Features

1. **Upload Notes**: Automatically extract and upload your Apple Notes to a vector store for AI processing.
2. **Semantic Search**: Perform intelligent searches across your notes using natural language queries and find matches.
3. **Ask Questions**: Get answers to specific questions using the information in your notes.
4. **Interactive Chat**: Engage in a conversation about your notes with an AI assistant.

## Installation

1. Ensure you have Python 3.7+ installed on your macOS system.
2. Clone this repository:
3. Install the required dependencies: pip install -r requirements.txt

## Configuration

On first run, the application will prompt you for your OpenAI API key. This key is stored locally in a configuration file for future use.

## Usage

Run the application by executing: python main.py start-shell

You'll be presented with a welcome screen and a list of available commands.

### Commands

- **upload**: This command extracts your Apple Notes and adds them to the AI's vector store. Run this command periodically to keep your AI up-to-date with your latest notes.

- **search**: Perform a semantic search across your notes. The AI will return the most relevant notes based on your query, with hyperlinks to those notes.

- **ask**: Ask a specific question about your notes. The AI will provide an answer based on the information in your notes.

- **chat**: Start an interactive chat session with the AI about your notes. This allows for a more dynamic exploration of your information.

- **help**: Display the list of available commands.

- **quit**: Exit the application.

## How It Works

1. **Note Extraction**: The application uses AppleScript to extract notes from the Apple Notes application.

2. **Vector Store**: Extracted notes are processed and stored in a vector database, allowing for efficient semantic searching.

3. **OpenAI Integration**: The application uses OpenAI's GPT model to understand and respond to your queries and conversations.

4. **Interactive CLI**: The Typer library is used to create an intuitive command-line interface for interacting with your notes.

## Privacy and Security

- Your notes are processed locally and only uploaded to OpenAI's servers for AI processing.
- Your OpenAI API key is stored locally in a configuration file.
- Ensure you have appropriate permissions set for the application to access your Notes database.

## Troubleshooting

- If you encounter permission issues, make sure to grant terminal disk access privileges in your macOS settings.
- For any other issues, please check the error message and ensure your OpenAI API key is valid and has sufficient credits.

## Contributing

Contributions to Chat Apple Notes are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is not officially associated with Apple or OpenAI. Use at your own discretion and ensure you comply with Apple's terms of service and OpenAI's use policies.