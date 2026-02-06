# Test files for Document Translator

This folder contains sample documents in **all supported formats**, with the same content: the **first canto (Canto I) of the Divina Commedia – Inferno** by Dante Alighieri, in Italian.

## Files (one per supported format)

| Format | File |
|--------|------|
| PDF | `divina_commedia_canto1.pdf` |
| Markdown | `divina_commedia_canto1.md` |
| Plain text | `divina_commedia_canto1.txt` |
| JSON | `divina_commedia_canto1.json` |
| XML | `divina_commedia_canto1.xml` |
| Word | `divina_commedia_canto1.docx` |
| PowerPoint | `divina_commedia_canto1.pptx` |

Use these to:

- Manually test upload, translation, and download for each format
- Verify extraction and output for PDF, DOCX, PPTX, etc.
- Run automated tests or scripts that need real multi-format samples

## Regenerating PDF, DOCX, PPTX

The `.pdf`, `.docx`, and `.pptx` files are generated from the `.txt` content by the backend’s `FileProcessor`. To regenerate them (e.g. after changing the text):

From the **project root** (with the backend virtual environment activated):

```bash
python test-files/generate_binary_formats.py
```

Requires backend dependencies: `pypdf`, `reportlab`, `python-docx`, `python-pptx` (see `backend/requirements.txt`).

## Source

The Italian text is the first canto of Dante’s *Inferno* (Divina Commedia), in the public domain (e.g. Wikisource).
