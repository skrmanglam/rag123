import os
from pathlib import Path
from typing import List, Dict, Tuple, Any
import fitz  # PyMuPDF


class DocumentLoader:
    """Load and extract text from various document formats."""
    
    SUPPORTED_FORMATS = {'.pdf', '.txt', '.md'}
    
    def __init__(self, upload_dir: str = "storage/uploaded_files"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    def is_supported(self, filename: str) -> bool:
        """Check if file format is supported."""
        ext = Path(filename).suffix.lower()
        return ext in self.SUPPORTED_FORMATS
    
    def save_file(self, file_content: bytes, filename: str, bot_id: str) -> str:
        """Save uploaded file to storage."""
        bot_dir = os.path.join(self.upload_dir, bot_id)
        os.makedirs(bot_dir, exist_ok=True)
        
        file_path = os.path.join(bot_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
    
    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF with page numbers.
        Returns list of dicts with 'page_number' and 'text'.
        """
        pages = []
        
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():  # Only include pages with text
                    pages.append({
                        'page_number': page_num + 1,
                        'text': text
                    })
            
            doc.close()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        
        return pages
    
    def extract_text_from_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from TXT file.
        Returns list with single dict containing all text.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return [{
                'page_number': None,
                'text': text
            }]
        except Exception as e:
            raise Exception(f"Error reading TXT file: {str(e)}")
    
    def extract_text_from_md(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from Markdown file.
        Returns list with single dict containing all text.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return [{
                'page_number': None,
                'text': text
            }]
        except Exception as e:
            raise Exception(f"Error reading MD file: {str(e)}")
    
    def load_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load document and extract text based on file type.
        Returns list of page/section dicts with text.
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext == '.txt':
            return self.extract_text_from_txt(file_path)
        elif ext == '.md':
            return self.extract_text_from_md(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def delete_bot_files(self, bot_id: str) -> bool:
        """Delete all uploaded files for a bot."""
        import shutil
        bot_dir = os.path.join(self.upload_dir, bot_id)
        if os.path.exists(bot_dir):
            try:
                shutil.rmtree(bot_dir)
                return True
            except Exception as e:
                print(f"Error deleting bot files: {e}")
                return False
        return True  # Directory doesn't exist, consider it deleted
