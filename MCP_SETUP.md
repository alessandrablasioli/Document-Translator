# MCP Server Setup Guide

This document explains how to use the Document Translator MCP server with Cursor and other MCP-compatible tools.

## Is MCP well integrated?

**Yes.** The MCP server uses the **same services** as the web app:

- **AgentTranslationService** – same translation and chunking logic as the API
- **FileProcessor** – same extraction and output for PDF, DOCX, MD, TXT, JSON, XML

So when Cursor (or another client) calls an MCP tool, it goes through the same backend logic as the Document Translator UI.

## Attaching the service for effective presence

You can make MCP’s presence effective in two ways:

1. **Stdio (recommended for Cursor)**  
   Run `python mcp_server.py` and add it to Cursor’s MCP config. Cursor spawns the process and talks over stdin/stdout. The script runs a **stdio transport loop** so it stays running and handles `initialize`, `tools/list`, and `tools/call`.

2. **HTTP on the running backend**  
   The FastAPI app exposes **POST /mcp** as an MCP JSON-RPC endpoint. If your client supports MCP over HTTP, point it at `http://localhost:8000/mcp` (or your backend URL). One running backend then serves both the web app and MCP.

## What is MCP?

Model Context Protocol (MCP) is a protocol that allows AI assistants and tools to communicate and share capabilities. The Document Translator MCP server exposes translation capabilities as tools that can be used from Cursor, Claude Desktop, and other MCP-compatible applications.

## Available MCP Tools

The Document Translator MCP server provides three tools:

### 1. `translate_text`
Translate text to a target language.

**Parameters:**
- `text` (required): Text to translate
- `target_language` (required): Target language (e.g., "Spanish", "French", "German")
- `source_language` (optional): Source language (auto-detected if not provided)

**Example:**
```json
{
  "name": "translate_text",
  "arguments": {
    "text": "Hello, world!",
    "target_language": "Spanish"
  }
}
```

### 2. `translate_file`
Translate a document file to a target language.

**Parameters:**
- `file_path` (required): Path to the file to translate
- `target_language` (required): Target language
- `output_path` (optional): Output path (auto-generated if not provided)

**Example:**
```json
{
  "name": "translate_file",
  "arguments": {
    "file_path": "/path/to/document.pdf",
    "target_language": "French",
    "output_path": "/path/to/document_fr.pdf"
  }
}
```

### 3. `extract_text_from_file`
Extract text content from a document file.

**Parameters:**
- `file_path` (required): Path to the file

**Example:**
```json
{
  "name": "extract_text_from_file",
  "arguments": {
    "file_path": "/path/to/document.pdf"
  }
}
```

## Setting Up MCP Server in Cursor (stdio)

1. **From the project root**, configure Cursor to spawn the MCP server over stdio:
   - Open Cursor MCP settings (e.g. `.cursor/mcp.json` or Cursor Settings → MCP).
   - Add the Document Translator server (use the **absolute path** to your `backend` folder):
     ```json
     {
       "mcpServers": {
         "document-translator": {
           "command": "python",
           "args": ["C:/Users/YourUser/Desktop/Document Translator/backend/mcp_server.py"]
         }
       }
     }
     ```
   - On Windows use forward slashes or escaped backslashes; replace `YourUser` with your username.

2. **Restart Cursor** so it starts the MCP server process. The server runs a stdio loop and handles `initialize`, `tools/list`, and `tools/call`.

3. **Use the tools in Cursor**:
   - The tools appear in Cursor’s MCP/connectors (e.g. “Add files, connectors, and more”).
   - Example: “Translate the file at path/to/document.pdf to Spanish” or “Translate this text to French.”

## Running the MCP Server (stdio) Standalone

```bash
cd backend
python mcp_server.py
```

The server will:
- Run a stdio loop (read JSON-RPC from stdin, write responses to stdout)
- Handle `initialize`, `tools/list`, and `tools/call`
- Log to stderr only so stdout stays clean for the protocol

Do not use this for interactive testing; use Cursor or another MCP client.

## Using MCP over HTTP (attach to running backend)

If your backend is already running (e.g. `uvicorn main:app`), MCP is available at:

- **URL:** `POST http://localhost:8000/mcp`
- **Body:** JSON-RPC object, e.g. `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}`

Same tools and logic as the stdio server; one process serves both the web API and MCP.

## MCP Protocol Support

The server implements the MCP protocol with:
- `tools/list`: List available tools
- `tools/call`: Call a tool with arguments
- Error handling and proper response formatting

## Integration Examples

### From Cursor

```
User: "Translate the file at ./document.pdf to Spanish"
Cursor: [Uses translate_file tool]
Result: Translated file created at ./document_translated.pdf
```

### From Claude Desktop

The MCP server can be configured in Claude Desktop's settings to enable translation capabilities.

## Troubleshooting

1. **Server not starting**: Check that Python dependencies are installed
2. **Tools not appearing**: Verify MCP server configuration in Cursor
3. **Translation errors**: Check OpenAI API key is set in `.env`

## Next Steps

- Add more tools (e.g., batch translation, language detection)
- Integrate with more MCP-compatible tools
- Add authentication for production use

