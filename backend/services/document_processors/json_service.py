from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class JSONService:
    """Service for JSON file extraction and generation"""
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text content from a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert JSON to readable text format
                return json.dumps(data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {e}")
            raise Exception(f"Invalid JSON file: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            raise Exception(f"Failed to extract text from JSON file: {str(e)}")
    
    def create_file_from_text(self, text: str, output_path: Path):
        """Create a JSON file from text content"""
        try:
            # Try to parse as JSON and save formatted
            try:
                data = json.loads(text)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # If not valid JSON, save as text
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
            logger.info(f"JSON file created successfully at {output_path}")
        except Exception as e:
            logger.error(f"Error creating JSON file: {e}")
            raise Exception(f"Failed to create JSON file: {str(e)}")

