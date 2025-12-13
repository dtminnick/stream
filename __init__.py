"""
Stream SOP Processor Module

This module provides functionality to:
- Read documents from folder structures
- Extract process flow structures using LLMs
- Store structured data in a database
"""

from .document_reader import DocumentReader
from .llm_extractor import FlowExtractor
from .flow_database import FlowDatabase

__all__ = ['DocumentReader', 'ProcessFlowExtractor', 'FlowDatabase']
