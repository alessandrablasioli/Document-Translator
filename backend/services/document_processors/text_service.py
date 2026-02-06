from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TextService:
    """Service for plain text file extraction and generation"""
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text content from a plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            raise Exception(f"Failed to extract text from text file: {str(e)}")
    
    def create_file_from_text(self, text: str, output_path: Path):
        """Create a text file from text content"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Text file created successfully at {output_path}")
        except Exception as e:
            logger.error(f"Error creating text file: {e}")
            raise Exception(f"Failed to create text file: {str(e)}")

