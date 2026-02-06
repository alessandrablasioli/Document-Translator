"""
Unit tests for FileProcessor: extract_text, create_output_file, get_file_type.
"""
import pytest
from pathlib import Path
import tempfile
import sys

# Ensure backend root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from services.file_processor import FileProcessor


@pytest.fixture
def file_processor():
    return FileProcessor()


class TestGetFileType:
    def test_returns_extension_for_supported_types(self, file_processor):
        assert file_processor.get_file_type(Path("doc.pdf")) == ".pdf"
        assert file_processor.get_file_type(Path("readme.md")) == ".md"
        assert file_processor.get_file_type(Path("data.txt")) == ".txt"
        assert file_processor.get_file_type(Path("config.json")) == ".json"
        assert file_processor.get_file_type(Path("doc.xml")) == ".xml"
        assert file_processor.get_file_type(Path("report.docx")) == ".docx"
        assert file_processor.get_file_type(Path("slides.pptx")) == ".pptx"

    def test_returns_none_for_unsupported_type(self, file_processor):
        assert file_processor.get_file_type(Path("file.csv")) is None
        assert file_processor.get_file_type(Path("file")) is None
        assert file_processor.get_file_type(Path("file.PDF")) == ".pdf"  # lowercased


class TestExtractText:
    def test_extract_txt(self, file_processor, tmp_path):
        f = tmp_path / "sample.txt"
        f.write_text("Hello world\nSecond line", encoding="utf-8")
        text, ext = file_processor.extract_text(f)
        assert ext == ".txt"
        assert "Hello world" in text
        assert "Second line" in text

    def test_extract_md(self, file_processor, tmp_path):
        f = tmp_path / "sample.md"
        f.write_text("# Title\n\nParagraph.", encoding="utf-8")
        text, ext = file_processor.extract_text(f)
        assert ext == ".md"
        assert "Title" in text
        assert "Paragraph" in text

    def test_unsupported_type_raises(self, file_processor, tmp_path):
        f = tmp_path / "file.csv"
        f.write_text("a,b,c")
        with pytest.raises(Exception) as exc_info:
            file_processor.extract_text(f)
        assert "Unsupported" in str(exc_info.value)

    def test_missing_file_raises(self, file_processor, tmp_path):
        missing = tmp_path / "nonexistent.txt"
        with pytest.raises(Exception) as exc_info:
            file_processor.extract_text(missing)
        assert "not found" in str(exc_info.value).lower() or "File" in str(exc_info.value)


class TestCreateOutputFile:
    def test_create_txt(self, file_processor, tmp_path):
        out = tmp_path / "out.txt"
        file_processor.create_output_file("Translated content", ".txt", out)
        assert out.exists()
        assert out.read_text(encoding="utf-8") == "Translated content"

    def test_create_md(self, file_processor, tmp_path):
        out = tmp_path / "out.md"
        file_processor.create_output_file("# Hola", ".md", out)
        assert out.exists()
        assert "# Hola" in out.read_text(encoding="utf-8")

    def test_unknown_extension_fallback_to_plain_text(self, file_processor, tmp_path):
        out = tmp_path / "out.xyz"
        file_processor.create_output_file("Fallback text", ".xyz", out)
        assert out.exists()
        assert out.read_text(encoding="utf-8") == "Fallback text"
