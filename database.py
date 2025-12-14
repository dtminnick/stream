"""
Database Storage Module

Stores extracted process flow data in a database table.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """
    Manages database storage for process flow data.
    """
    
    def __init__(self, db_path: str = "stream.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
    
    def insert_process_flow(self, process_flow: Dict[str, Any]) -> int:
        """
        Insert a process flow into the database.
        
        Args:
            process_flow: Dictionary containing process flow data
            
        Returns:
            ID of the inserted process flow
        """
        cursor = self.conn.cursor()
        
        # Insert main process flow record
        cursor.execute("""
            INSERT INTO process (
                process_name, 
                process_description, 
                source_document,
                document_path, 
                extraction_model
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            process_flow.get('process_name', ''),
            process_flow.get('process_description', ''),
            process_flow.get('source_document', ''),
            process_flow.get('document_path', ''),
            process_flow.get('extraction_model', ''),
        ))
        
        process_id = cursor.lastrowid
        
        # Insert steps
        steps = process_flow.get('steps', [])
        for step in steps:
            cursor.execute("""
                INSERT INTO step (
                    process_id, 
                    step_number, 
                    step_name, 
                    step_description,
                    responsible_role, 
                    inputs, 
                    outputs, 
                    tools,
                    decision_points, 
                    next_steps
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                process_id,
                step.get('step_number', 0),
                step.get('step_name', ''),
                step.get('description', ''),
                step.get('responsible_role', ''),
                ", ".join(step.get('inputs', [])),
                ", ".join(step.get('outputs', [])),
                ", ".join(step.get('tools', [])),
                ", ".join(step.get('decision_points', [])),
                ", ".join(map(str, step.get('next_steps', [])))
            ))
        
        self.conn.commit()
        logger.info(f"Inserted process flow: {process_flow.get('process_name')} (ID: {process_id})")
        return process_id
    
    def insert_multiple(self, process_flows: List[Dict[str, Any]]) -> List[int]:
        """
        Insert multiple process flows into the database.
        
        Args:
            process_flows: List of process flow dictionaries
            
        Returns:
            List of inserted process flow IDs
        """
        ids = []
        for flow in process_flows:
            try:
                flow_id = self.insert_process_flow(flow)
                ids.append(flow_id)
            except Exception as e:
                logger.error(f"Failed to insert process flow: {e}")
                continue
        return ids
    
    def list_all_processes(self) -> List[Dict[str, Any]]:
        """
        List all process flows in the database.
        
        Returns:
            List of process flow summaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT process_id, process_name, process_description, source_document,
                   extraction_timestamp, created_at
            FROM process
            ORDER BY created_at DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

