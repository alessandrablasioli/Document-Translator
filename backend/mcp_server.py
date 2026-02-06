"""
MCP (Model Context Protocol) Server for Document Translator
Enables translation capabilities from Cursor and other MCP-compatible tools.
Uses the same AgentTranslationService and FileProcessor as the FastAPI app.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.agent_translation_service import AgentTranslationService
from services.file_processor import FileProcessor

# Stdio transport: only stderr for logs so stdout stays clean for JSON-RPC
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,
    force=True,
)
logger = logging.getLogger(__name__)


class DocumentTranslatorMCPServer:
    """
    MCP Server implementation for document translation.
    Provides tools for translating documents via MCP protocol.
    """
    
    def __init__(self):
        self.translation_service = AgentTranslationService()
        self.file_processor = FileProcessor()
    
    async def translate_text(
        self, 
        text: str, 
        target_language: str, 
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language (e.g., "Spanish", "French")
            source_language: Optional source language
            
        Returns:
            Dictionary with translated text and metadata
        """
        try:
            translated = self.translation_service.translate(
                text, 
                target_language, 
                source_language
            )
            return {
                "success": True,
                "translated_text": translated,
                "original_length": len(text),
                "translated_length": len(translated),
                "target_language": target_language
            }
        except Exception as e:
            logger.error(f"MCP translate_text error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def translate_file(
        self,
        file_path: str,
        target_language: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate a document file.
        
        Args:
            file_path: Path to the file to translate
            target_language: Target language
            output_path: Optional output path (auto-generated if not provided)
            
        Returns:
            Dictionary with translation status and output path
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            # Extract text
            text_content, file_ext = self.file_processor.extract_text(path)
            
            # Translate
            translated_text = self.translation_service.translate(
                text_content,
                target_language
            )
            
            # Generate output path if not provided
            if not output_path:
                output_path = str(path.parent / f"{path.stem}_translated{file_ext}")
            
            # Create translated file
            output = Path(output_path)
            self.file_processor.create_output_file(
                translated_text,
                file_ext,
                output
            )
            
            return {
                "success": True,
                "output_path": str(output),
                "file_type": file_ext,
                "original_length": len(text_content),
                "translated_length": len(translated_text)
            }
        except Exception as e:
            logger.error(f"MCP translate_file error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_text_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a document file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            text_content, file_ext = self.file_processor.extract_text(path)
            
            return {
                "success": True,
                "text": text_content,
                "file_type": file_ext,
                "char_count": len(text_content),
                "word_count": len(text_content.split())
            }
        except Exception as e:
            logger.error(f"MCP extract_text error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available MCP tools.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "translate_text",
                "description": "Translate text to a target language",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to translate"
                        },
                        "target_language": {
                            "type": "string",
                            "description": "Target language (e.g., 'Spanish', 'French', 'German')"
                        },
                        "source_language": {
                            "type": "string",
                            "description": "Optional source language (auto-detected if not provided)",
                            "required": False
                        }
                    },
                    "required": ["text", "target_language"]
                }
            },
            {
                "name": "translate_file",
                "description": "Translate a document file to a target language",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to translate"
                        },
                        "target_language": {
                            "type": "string",
                            "description": "Target language (e.g., 'Spanish', 'French', 'German')"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional output path (auto-generated if not provided)",
                            "required": False
                        }
                    },
                    "required": ["file_path", "target_language"]
                }
            },
            {
                "name": "extract_text_from_file",
                "description": "Extract text content from a document file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        ]
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP protocol request.
        Supports: initialize, tools/list, tools/call.
        """
        method = request.get("method")
        params = request.get("params") or {}
        
        try:
            if method == "initialize":
                return {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                    },
                    "serverInfo": {
                        "name": "document-translator",
                        "version": "1.0.0",
                        "description": "Document Translator: translate text and files using the same backend as the web app.",
                    },
                    "instructions": "Use translate_text, translate_file, or extract_text_from_file to translate or extract content.",
                }
            
            if method == "tools/list":
                tools = self.get_tools()
                return {"tools": [self._to_mcp_tool(t) for t in tools]}
            
            if method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments") or {}
                
                if tool_name == "translate_text":
                    result = await self.translate_text(
                        arguments.get("text", ""),
                        arguments.get("target_language", ""),
                        arguments.get("source_language"),
                    )
                elif tool_name == "translate_file":
                    result = await self.translate_file(
                        arguments.get("file_path", ""),
                        arguments.get("target_language", ""),
                        arguments.get("output_path"),
                    )
                elif tool_name == "extract_text_from_file":
                    result = await self.extract_text_from_file(
                        arguments.get("file_path", "")
                    )
                else:
                    return {
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}",
                        }
                    }
                
                return {
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2)}
                    ]
                }
            
            return {
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}",
                }
            }
        
        except Exception as e:
            logger.error("MCP request error: %s", e, exc_info=True)
            return {
                "error": {
                    "code": -32603,
                    "message": str(e),
                }
            }
    
    def _to_mcp_tool(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal tool def to MCP tools/list item (name, description, inputSchema)."""
        return {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "inputSchema": tool.get("inputSchema", {"type": "object", "properties": {}}),
        }


# MCP Server instance (shared for stdio and HTTP)
mcp_server = DocumentTranslatorMCPServer()


def run_stdio_server():
    """
    Run MCP server over stdio so Cursor/Claude can spawn this process and
    communicate via stdin/stdout. Do not write anything to stdout except
    JSON-RPC response lines.
    """
    server = DocumentTranslatorMCPServer()
    logger.info("Document Translator MCP server running on stdio")

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON: %s", e)
            _send_json_rpc_error(sys.stdout, None, -32700, "Parse error")
            continue

        req_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params") or {}

        if method == "notifications/initialized":
            continue

        try:
            result = asyncio.run(server.handle_mcp_request({"method": method, "params": params}))
        except Exception as e:
            logger.exception("Request failed")
            _send_json_rpc_error(sys.stdout, req_id, -32603, str(e))
            continue

        if "error" in result:
            _send_json_rpc_error(
                sys.stdout,
                req_id,
                result["error"].get("code", -32603),
                result["error"].get("message", "Unknown error"),
            )
        else:
            _send_json_rpc_result(sys.stdout, req_id, result)
        sys.stdout.flush()


def _send_json_rpc_result(stream, req_id: Any, result: Dict[str, Any]) -> None:
    stream.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}) + "\n")


def _send_json_rpc_error(stream, req_id: Any, code: int, message: str) -> None:
    stream.write(
        json.dumps(
            {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
        )
        + "\n"
    )


if __name__ == "__main__":
    run_stdio_server()

