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


class FlowDatabase:
    """
    Manages database storage for process flow data.
    """
    
    def __init__(self, db_path: str = "process_flows.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Main process flows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_name TEXT NOT NULL,
                process_description TEXT,
                source_document TEXT NOT NULL,
                document_path TEXT,
                document_relative_path TEXT,
                extraction_model TEXT,
                extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Process steps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_flow_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                step_name TEXT NOT NULL,
                description TEXT,
                responsible_role TEXT,
                inputs TEXT,
                outputs TEXT,
                decision_points TEXT,
                next_steps TEXT,
                FOREIGN KEY (process_flow_id) REFERENCES process_flows(id) ON DELETE CASCADE
            )
        """)
        
        # Roles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_flow_id INTEGER NOT NULL,
                role_name TEXT NOT NULL,
                FOREIGN KEY (process_flow_id) REFERENCES process_flows(id) ON DELETE CASCADE
            )
        """)
        
        # Tools and systems table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_flow_id INTEGER NOT NULL,
                tool_name TEXT NOT NULL,
                FOREIGN KEY (process_flow_id) REFERENCES process_flows(id) ON DELETE CASCADE
            )
        """)
        
        # Compliance requirements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_flow_id INTEGER NOT NULL,
                requirement TEXT NOT NULL,
                FOREIGN KEY (process_flow_id) REFERENCES process_flows(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_process_flows_document 
            ON process_flows(source_document)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_process_steps_flow 
            ON process_steps(process_flow_id)
        """)
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
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
            INSERT INTO process_flows (
                process_name, process_description, source_document,
                document_path, document_relative_path, extraction_model,
                raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            process_flow.get('process_name', ''),
            process_flow.get('process_description', ''),
            process_flow.get('source_document', ''),
            process_flow.get('document_path', ''),
            process_flow.get('document_relative_path', ''),
            process_flow.get('extraction_model', ''),
            json.dumps(process_flow)  # Store raw JSON for reference
        ))
        
        process_flow_id = cursor.lastrowid
        
        # Insert steps
        steps = process_flow.get('steps', [])
        for step in steps:
            cursor.execute("""
                INSERT INTO process_steps (
                    process_flow_id, step_number, step_name, description,
                    responsible_role, inputs, outputs, decision_points, next_steps
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                process_flow_id,
                step.get('step_number', 0),
                step.get('step_name', ''),
                step.get('description', ''),
                step.get('responsible_role', ''),
                json.dumps(step.get('inputs', [])),
                json.dumps(step.get('outputs', [])),
                json.dumps(step.get('decision_points', [])),
                json.dumps(step.get('next_steps', []))
            ))
        
        # Insert roles
        roles = process_flow.get('roles', [])
        for role in roles:
            cursor.execute("""
                INSERT INTO process_roles (process_flow_id, role_name)
                VALUES (?, ?)
            """, (process_flow_id, role))
        
        # Insert tools/systems
        tools = process_flow.get('tools_systems', [])
        for tool in tools:
            cursor.execute("""
                INSERT INTO process_tools (process_flow_id, tool_name)
                VALUES (?, ?)
            """, (process_flow_id, tool))
        
        # Insert compliance requirements
        compliance = process_flow.get('compliance_requirements', [])
        for req in compliance:
            cursor.execute("""
                INSERT INTO compliance_requirements (process_flow_id, requirement)
                VALUES (?, ?)
            """, (process_flow_id, req))
        
        self.conn.commit()
        logger.info(f"Inserted process flow: {process_flow.get('process_name')} (ID: {process_flow_id})")
        return process_flow_id
    
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
    
    def get_process_flow(self, process_flow_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a process flow by ID.
        
        Args:
            process_flow_id: ID of the process flow
            
        Returns:
            Dictionary containing process flow data, or None if not found
        """
        cursor = self.conn.cursor()
        
        # Get main record
        cursor.execute("SELECT * FROM process_flows WHERE id = ?", (process_flow_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        # Reconstruct from raw_data or build from tables
        raw_data = json.loads(row['raw_data'])
        return raw_data
    
    def list_all_processes(self) -> List[Dict[str, Any]]:
        """
        List all process flows in the database.
        
        Returns:
            List of process flow summaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, process_name, process_description, source_document,
                   extraction_timestamp, created_at
            FROM process_flows
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

