import csv
import os
from typing import List, Dict, Any
from pathlib import Path
import uuid


class FAQLoader:
    """Load and parse FAQ CSV files."""
    
    def __init__(self, upload_dir: str = "storage/faq_files"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, bot_id: str) -> str:
        """Save uploaded FAQ CSV file to storage."""
        bot_dir = os.path.join(self.upload_dir, bot_id)
        os.makedirs(bot_dir, exist_ok=True)
        
        file_path = os.path.join(bot_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
    
    def parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse FAQ CSV file.
        
        Expected CSV format:
        question_id,question,answer
        
        Optional columns: category, metadata
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of FAQ entry dicts
        """
        faq_entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                # Detect delimiter (comma or pipe)
                delimiter = ',' if ',' in sample else '|'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # Validate required columns
                required_columns = {'question_id', 'question', 'answer'}
                if not required_columns.issubset(set(reader.fieldnames or [])):
                    raise ValueError(
                        f"CSV must contain columns: {required_columns}. "
                        f"Found: {reader.fieldnames}"
                    )
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    # Skip empty rows
                    if not row.get('question', '').strip():
                        continue
                    
                    # Validate required fields
                    question_id = row.get('question_id', '').strip()
                    question = row.get('question', '').strip()
                    answer = row.get('answer', '').strip()
                    
                    if not question_id:
                        raise ValueError(f"Row {row_num}: question_id is required")
                    if not question:
                        raise ValueError(f"Row {row_num}: question is required")
                    if not answer:
                        raise ValueError(f"Row {row_num}: answer is required")
                    
                    faq_entry = {
                        'question_id': question_id,
                        'question': question,
                        'answer': answer,
                        'category': row.get('category', '').strip() or None,
                    }
                    
                    faq_entries.append(faq_entry)
            
            if not faq_entries:
                raise ValueError("CSV file contains no valid FAQ entries")
            
            return faq_entries
            
        except csv.Error as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error reading FAQ file: {str(e)}")
    
    def validate_faq_entries(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate FAQ entries for duplicates and issues.
        
        Args:
            entries: List of FAQ entry dicts
            
        Returns:
            Validation result with stats and warnings
        """
        question_ids = set()
        questions = set()
        duplicates = []
        warnings = []
        
        for entry in entries:
            question_id = entry['question_id']
            question = entry['question'].lower()
            
            # Check for duplicate question_ids
            if question_id in question_ids:
                duplicates.append(f"Duplicate question_id: {question_id}")
            question_ids.add(question_id)
            
            # Check for very similar questions (exact match)
            if question in questions:
                warnings.append(f"Similar question found: {entry['question']}")
            questions.add(question)
            
            # Check answer length
            if len(entry['answer']) < 10:
                warnings.append(f"Short answer for question_id {question_id}")
        
        return {
            'valid': len(duplicates) == 0,
            'total_entries': len(entries),
            'unique_question_ids': len(question_ids),
            'duplicates': duplicates,
            'warnings': warnings
        }
    
    def delete_bot_faq_files(self, bot_id: str) -> bool:
        """Delete all FAQ files for a bot."""
        import shutil
        bot_dir = os.path.join(self.upload_dir, bot_id)
        if os.path.exists(bot_dir):
            try:
                shutil.rmtree(bot_dir)
                return True
            except Exception as e:
                print(f"Error deleting bot FAQ files: {e}")
                return False
        return True  # Directory doesn't exist, consider it deleted