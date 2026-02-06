"""
Service for extracting text from and creating PowerPoint (.pptx) files.
"""
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class PPTXService:
    """Service for handling PowerPoint (.pptx) files"""
    
    def extract_text(self, file_path: Path) -> str:
        """
        Extract text content from a PowerPoint file.
        
        Args:
            file_path: Path to the .pptx file
            
        Returns:
            Extracted text content
        """
        try:
            from pptx import Presentation
            
            presentation = Presentation(file_path)
            text_content = []
            
            # Extract text from all slides
            for slide_num, slide in enumerate(presentation.slides, 1):
                slide_text = []
                
                # Extract text from all shapes on the slide
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        slide_text.append(shape.text.strip())
                
                if slide_text:
                    text_content.append(f"--- Slide {slide_num} ---")
                    text_content.extend(slide_text)
                    text_content.append("")  # Empty line between slides
            
            extracted_text = "\n".join(text_content)
            
            if not extracted_text.strip():
                raise Exception("No text content found in PowerPoint file")
            
            logger.info(f"Extracted {len(presentation.slides)} slides from PowerPoint file")
            return extracted_text
            
        except ImportError:
            raise Exception(
                "python-pptx library is required for PowerPoint support. "
                "Install it with: pip install python-pptx"
            )
        except Exception as e:
            logger.error(f"Error extracting text from PowerPoint: {e}")
            raise Exception(f"Failed to extract text from PowerPoint file: {str(e)}")
    
    def create_file_from_text(self, text: str, output_path: Path):
        """
        Create a PowerPoint file from text content.
        Splits text into slides based on "--- Slide X ---" markers or paragraph breaks.
        
        Args:
            text: Text content to convert to PowerPoint
            output_path: Path where the .pptx file should be created
        """
        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt
            
            presentation = Presentation()
            
            # Split text into slides
            # First, check if text has slide markers
            if "--- Slide" in text:
                # Split by slide markers
                slides_content = []
                current_slide = []
                
                for line in text.split('\n'):
                    if line.strip().startswith('--- Slide'):
                        if current_slide:
                            slides_content.append('\n'.join(current_slide))
                        current_slide = []
                    elif line.strip():
                        current_slide.append(line.strip())
                
                if current_slide:
                    slides_content.append('\n'.join(current_slide))
            else:
                # Split by double newlines (paragraph breaks) as slides
                slides_content = [slide.strip() for slide in text.split('\n\n') if slide.strip()]
            
            # If no slides found, create one slide with all text
            if not slides_content:
                slides_content = [text]
            
            # Create slides from content
            for slide_content in slides_content:
                # Remove slide markers if present
                slide_content = slide_content.replace('--- Slide', '').replace('---', '').strip()
                
                if not slide_content:
                    continue
                
                slide = presentation.slides.add_slide(presentation.slide_layouts[5])  # Blank layout
                
                # Split content into paragraphs and add as text boxes
                paragraphs = slide_content.split('\n')
                
                # Create a text box for the slide
                left = Inches(0.5)
                top = Inches(1)
                width = Inches(9)
                height = Inches(6)
                
                text_box = slide.shapes.add_textbox(left, top, width, height)
                text_frame = text_box.text_frame
                text_frame.word_wrap = True
                
                # Add paragraphs
                for i, para_text in enumerate(paragraphs):
                    if para_text.strip():
                        if i == 0:
                            p = text_frame.paragraphs[0]
                            p.text = para_text.strip()
                        else:
                            p = text_frame.add_paragraph()
                            p.text = para_text.strip()
                        
                        # Set font size
                        p.font.size = Pt(14)
            
            presentation.save(output_path)
            logger.info(f"PowerPoint file created successfully at {output_path} with {len(presentation.slides)} slides")
            
        except ImportError:
            raise Exception(
                "python-pptx library is required for PowerPoint creation. "
                "Install it with: pip install python-pptx"
            )
        except Exception as e:
            logger.error(f"Error creating PowerPoint file: {e}")
            raise Exception(f"Failed to create PowerPoint file: {str(e)}")

