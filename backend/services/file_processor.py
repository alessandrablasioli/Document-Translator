from pathlib import Path
from typing import Tuple, Optional
import logging

from services.document_processors.pdf_service import PDFService
from services.document_processors.markdown_service import MarkdownService
from services.document_processors.text_service import TextService
from services.document_processors.json_service import JSONService
from services.document_processors.xml_service import XMLService
from services.document_processors.docx_service import DOCXService
from services.document_processors.pptx_service import PPTXService

logger = logging.getLogger(__name__)


class FileProcessor:
    """Service for processing different file types and extracting text content"""
    
    def __init__(self):
        # Initialize all document processors
        self.pdf_service = PDFService()
        self.markdown_service = MarkdownService()
        self.text_service = TextService()
        self.json_service = JSONService()
        self.xml_service = XMLService()
        self.docx_service = DOCXService()
        self.pptx_service = PPTXService()
        
        # Map extensions to their respective services
        self.supported_extensions = {
            '.pdf': (self.pdf_service, 'extract_text'),
            '.md': (self.markdown_service, 'extract_text'),
            '.txt': (self.text_service, 'extract_text'),
            '.json': (self.json_service, 'extract_text'),
            '.xml': (self.xml_service, 'extract_text'),
            '.docx': (self.docx_service, 'extract_text'),
            '.pptx': (self.pptx_service, 'extract_text'),
        }
        
        # Map extensions to their create methods
        self.create_methods = {
            '.pdf': (self.pdf_service, 'create_file_from_text'),
            '.md': (self.markdown_service, 'create_file_from_text'),
            '.txt': (self.text_service, 'create_file_from_text'),
            '.json': (self.json_service, 'create_file_from_text'),
            '.xml': (self.xml_service, 'create_file_from_text'),
            '.docx': (self.docx_service, 'create_file_from_text'),
            '.pptx': (self.pptx_service, 'create_file_from_text'),
        }
    
    def get_file_type(self, file_path: Path) -> Optional[str]:
        """Get file extension from file path"""
        ext = file_path.suffix.lower()
        return ext if ext in self.supported_extensions else None
    
    def extract_text(self, file_path: Path) -> Tuple[str, str]:
        """
        Extract text content from a file based on its type
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (text_content, file_extension)
            
        Raises:
            Exception if file type is not supported or extraction fails
        """
        file_type = self.get_file_type(file_path)
        
        if not file_type:
            supported = ', '.join(self.supported_extensions.keys())
            raise Exception(f"Unsupported file type. Supported types: {supported}")
        
        if not file_path.exists():
            raise Exception(f"File not found: {file_path}")
        
        try:
            service, method_name = self.supported_extensions[file_type]
            method = getattr(service, method_name)
            text_content = method(file_path)
            
            if not text_content or not text_content.strip():
                raise Exception(f"Could not extract text from {file_type} file")
            
            return text_content, file_type
        
        except Exception as e:
            logger.error(f"Error extracting text from {file_type} file: {e}")
            raise Exception(f"Failed to extract text from {file_type} file: {str(e)}")
    
    def create_output_file(self, text: str, original_extension: str, output_path: Path):
        """
        Create output file from translated text, preserving original format when possible
        
        Args:
            text: Translated text content
            original_extension: Original file extension
            output_path: Path where output file should be created
        """
        if original_extension not in self.create_methods:
            # Default: save as text file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.warning(f"Unknown extension {original_extension}, saved as text file")
            return
        
        try:
            service, method_name = self.create_methods[original_extension]
            method = getattr(service, method_name)
            method(text, output_path)
        except Exception as e:
            logger.error(f"Error creating {original_extension} file: {e}")
            # Fallback: save as text file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.warning(f"Failed to create {original_extension} file, saved as text instead")

