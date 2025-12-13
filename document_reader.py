
"""
Document Reader Module
======================

This module provides the `DocumentReader` class for reading and extracting text
from documents stored in a folder structure. It supports multiple file formats:

- PDF files (.pdf)
- Word documents (.docx)
- Text files (.txt)

Features:
---------
- Recursive or non-recursive search through directories
- Automatic detection of supported file types
- Extraction of text content with metadata (path, name, extension, relative path)
- Logging of successes and errors for traceability

Example:
--------
    >>> reader = DocumentReader(root_folder="data/documents", recursive=True)
    >>> docs = reader.read_all_documents()
    >>> print(docs[0]['content'])
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import logging
import PyPDF2
from docx import Document

logger = logging.getLogger(__name__)

class DocumentReader:
    """
    DocumentReader
    --------------

    A utility class for discovering and reading documents from a folder structure.
    Supports PDF, Word (.docx), and plain text (.txt) files.

    Attributes:
    -----------
    root_folder : Path
        Root folder path containing documents.
    recursive : bool
        Whether to search subdirectories recursively.
    supported_extensions : set
        File extensions supported by the reader.
    """

    supported_extensions = {'.pdf', '.docx', '.txt'}
    
    def __init__(self, root_folder: str, recursive: bool = True):
        """
        Initialize the DocumentReader.

        Parameters:
        -----------
        root_folder : str
            Root folder path containing documents.
        recursive : bool, optional (default=True)
            If True, search subdirectories recursively.

        Raises:
        -------
        ValueError
            If the provided root folder does not exist.
        """
        self.root_folder = Path(root_folder)

        if not self.root_folder.exists():
            raise ValueError(f"Folder does not exist: {root_folder}")
        
        self.recursive = recursive
    
    def find_documents(self) -> List[Path]:
        """
        Discover all supported documents in the folder structure.

        Returns:
        --------
        List[Path]
            A sorted list of file paths to supported documents.

        Notes:
        ------
        - Uses glob patterns for recursive or non-recursive search.
        - Logs the number of documents found.
        """
        documents = []
        
        pattern = "**/*" if self.recursive else "*"
        
        for file_path in self.root_folder.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                documents.append(file_path)
        
        logger.info(f"Found {len(documents)} documents in {self.root_folder}")
        return sorted(documents)
    
    def read_pdf(self, file_path: Path) -> str:
        """
        Extract text from a PDF file.

        Parameters:
        -----------
        file_path : Path
            Path to the PDF file.

        Returns:
        --------
        str
            Extracted text content.

        Raises:
        -------
        Exception
            If the PDF cannot be read or parsed.
        """
        text_content = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())
            return '\n'.join(text_content)
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            raise
    
    def read_docx(self, file_path: Path) -> str:
        """
        Extract text from a Word document (.docx).

        Parameters:
        -----------
        file_path : Path
            Path to the Word document.

        Returns:
        --------
        str
            Extracted text content.

        Raises:
        -------
        Exception
            If the docx file cannot be read or parsed.
        """
        try:
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs]
            return '\n'.join(paragraphs)
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            raise
    
    def read_txt(self, file_path: Path) -> str:
        """
        Read text from a plain text file (.txt).

        Parameters:
        -----------
        file_path : Path
            Path to the text file.

        Returns:
        --------
        str
            Extracted text content.

        Raises:
        -------
        Exception
            If the text file cannot be read.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {e}")
            raise
    
    def read_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Read a document and return its content with metadata.

        Parameters:
        -----------
        file_path : Path
            Path to the document.

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing:
            - 'path': Original file path (str)
            - 'name': File name (str)
            - 'extension': File extension (str)
            - 'content': Extracted text content (str)
            - 'relative_path': Path relative to root folder (str)

        Raises:
        -------
        ValueError
            If the file type is unsupported.
        """
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            content = self.read_pdf(file_path)
        elif extension == '.docx':
            content = self.read_docx(file_path)
        elif extension == '.txt':
            content = self.read_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'extension': extension,
            'content': content,
            'relative_path': str(file_path.relative_to(self.root_folder))
        }
    
    def read_all_documents(self) -> List[Dict[str, Any]]:
        """
        Read all supported documents from the folder structure.

        Returns:
        --------
        List[Dict[str, Any]]
            List of document dictionaries with metadata and content.

        Notes:
        ------
        - Skips documents that cannot be read, logging errors.
        - Useful for batch processing of entire directories.
        """
        documents = []
        file_paths = self.find_documents()
        
        for file_path in file_paths:
            try:
                doc_data = self.read_document(file_path)
                documents.append(doc_data)
                logger.info(f"Successfully read: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
                continue
        
        return documents
