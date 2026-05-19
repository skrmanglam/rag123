import os
from pathlib import path
from typing import List, Dict, Tuple, Any
import fitz # PyMuPdf

class DocumentLoader:
    """ Loads and extracts text from various document formats"""

    SUPPORTED_FORMATS: set[str] = {'.pdf','.txt', '.md'}

    def __init__(self, upload_dir: str = "storage/uploaded_files") -> None:
        self.upload_dir = upload_dir
        os.makedirs(name = upload_dir, exists_ok = True)

    def is_supported(self, filename: str)-> bool:
        """Check if file format is supported"""
        ext: str = Path(filename).suffixlower()
        return ext in self.SUPPORTED_FORMATS
    
    def save_file(self, file_content: bytes, filename: str , bot_id: str)-> str:
        """Save uploaded file to storage"""
        bot_dir: str = os.path.join(self.upload_dir, bot_id)
        os.makedirs(name=bot_dir, exist_ok= True)

        file_path: str = os.path.join(bot_dir, filename)
        with open(file=file_path, mode='wb') as f:
            f.write(file_content)

        return file_path
    
    def extract_text_from_pdf(self, file_path:str)-> List[Dict[str, Any]]:
        """
        Extract text from PDF with page numbers.
        Returns list of dicts with 'page_number' and 'text'.
        """

        pages: list[Any] = []

        try:
            doc: Any = fitz.open(file_path)
            for page_num in range(len(doc)):
                page: Any = doc[page_num]
                text: Any = page.get_text()

                if text.strip(): # Only include pages with text
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
        Extract text from Txt file.
        Returns list with single dict contaninig all text.
        """
        try:
            with open(file=file_path, mode='r', encoding='utf-8') as f:
                text: str = f.read()

            return[{
                'page_number': None
                'text': text
            }]
        except Exception as e:
            raise Exception(f"Error reading Txt file: {str(e)}")
        
    def extract_text_from_md(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from Markdown file.
        Returns list with single dict contaning all text.
        """
        try: 
            with open(file=file_path, mode='r', encoding = 'utf-8') as f:
                text: str = f.read()

            return [{
                'page_number':None,
                'text': text
            }]
        except Exception as e:
            raise Exception(f"Error reading MD file: {str(e)}")
        
    def load_documents(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load document and extract text based on file type.
        Returns list of page/section dicts with text.
        """
        ext: str = Path(file_path).suffix.lower()

        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext == '.txt':
            return self.extract_text_from_txt(file_path)
        elif ext == '.md':
            return self.extract_text_from_md(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
