from pathlib import Path
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class XMLService:
    """Service for XML file extraction and generation"""
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text content from an XML file"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract all text content from XML elements
            def extract_text_from_element(elem):
                text_parts = []
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
                for child in elem:
                    text_parts.append(extract_text_from_element(child))
                if elem.tail and elem.tail.strip():
                    text_parts.append(elem.tail.strip())
                return ' '.join(text_parts)
            
            return extract_text_from_element(root)
        except ET.ParseError as e:
            logger.error(f"Invalid XML file: {e}")
            raise Exception(f"Invalid XML file: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading XML file: {e}")
            raise Exception(f"Failed to extract text from XML file: {str(e)}")
    
    def create_file_from_text(self, text: str, output_path: Path):
        """Create an XML file from text content"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"XML file created successfully at {output_path}")
        except Exception as e:
            logger.error(f"Error creating XML file: {e}")
            raise Exception(f"Failed to create XML file: {str(e)}")

