from pathlib import Path
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import logging

logger = logging.getLogger(__name__)


class PDFService:
    """Service for PDF extraction and generation"""
    
    def extract_text(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text_content = []
            
            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue
            
            return "\n\n".join(text_content)
        
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def create_pdf_from_text(self, text: str, output_path: Path):
        """Create a PDF file from text content"""
        try:
            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Split text into paragraphs
            paragraphs = text.split('\n\n')
            
            for para in paragraphs:
                if para.strip():
                    # Create paragraph with proper styling
                    p = Paragraph(para.strip().replace('\n', '<br/>'), styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 0.2 * inch))
            
            doc.build(story)
            logger.info(f"PDF created successfully at {output_path}")
        
        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            raise Exception(f"Failed to create PDF: {str(e)}")

    def create_file_from_text(self, text: str, output_path: Path):
        """Create a PDF file from text (same interface as other document processors)."""
        self.create_pdf_from_text(text, output_path)

