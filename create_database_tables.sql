
CREATE TABLE IF NOT EXISTS stream (
	stream_id INTEGER PRIMARY KEY AUTOINCREMENT,
	level INTEGER NOT NULL,
	stream_name TEXT NOT NULL,
	parent_stream_id INTEGER,
	FOREIGN KEY (parent_stream_id) REFERENCES stream(stream_id)
	);

CREATE TABLE IF NOT EXISTS process (
	process_id INTEGER PRIMARY KEY AUTOINCREMENT,
	process_name TEXT NOT NULL,
	process_description TEXT NOT NULL,
	source_document TEXT NOT NULL,
	document_path TEXT NOT NULL,
	extraction_model TEXT,
	extraction_timestamp datetime DEFAULT CURRENT_TIMESTAMP,
	created_at datetime DEFAULT CURRENT_TIMESTAMP
	);
	
CREATE TABLE stream_process (
	stream_id INTEGER NOT NULL,
	process_id INTEGER NOT NULL,
	PRIMARY KEY (stream_id, process_id),
	FOREIGN KEY (stream_id) REFERENCES stream(stream_id),
	FOREIGN KEY (process_id) REFERENCES process(process_id)
	);
	
CREATE TABLE IF NOT EXISTS step (
	step_id INTEGER PRIMARY KEY AUTOINCREMENT,
	process_id INTEGER NOT NULL,
	step_number INTEGER NOT NULL,
	step_name TEXT NOT NULL,
	step_description TEXT NOT NULL,
	responsible_role TEXT,
	inputs TEXT,
	outputs TEXT,
	tools TEXT,
	decision_points TEXT,
	next_steps TEXT,
	FOREIGN KEY (process_id) REFERENCES process(process_id) ON DELETE CASCADE
	);
	
CREATE TABLE IF NOT EXISTS role (
	role_id INTEGER PRIMARY KEY AUTOINCREMENT,
	canonical_role_name TEXT NOT NULL UNIQUE
	);
	
CREATE TABLE IF NOT EXISTS role_alias (
	role_alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
	raw_name TEXT NOT NULL,
	role_id INTEGER NOT NULL,
	FOREIGN KEY (role_id) REFERENCES role(role_id)
	);
	
CREATE TABLE IF NOT EXISTS input (
	input_id INTEGER PRIMARY KEY AUTOINCREMENT,
	canonical_input_name TEXT NOT NULL UNIQUE
	);
	
CREATE TABLE IF NOT EXISTS input_alias (
	input_alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
	raw_name TEXT NOT NULL,
	input_id INTEGER NOT NULL,
	FOREIGN KEY (input_id) REFERENCES input(input_id)
	);
	
CREATE TABLE IF NOT EXISTS output (
	output_id INTEGER PRIMARY KEY AUTOINCREMENT,
	canonical_output_name TEXT NOT NULL UNIQUE
	);
	
CREATE TABLE IF NOT EXISTS output_alias (
	output_alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
	raw_name TEXT NOT NULL,
	output_id INTEGER NOT NULL,
	FOREIGN KEY (output_id) REFERENCES output(output_id)
	);
	
CREATE TABLE IF NOT EXISTS tool (
	tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
	canonical_tool_name TEXT NOT NULL UNIQUE
	);
	
CREATE TABLE IF NOT EXISTS tool_alias (
	tool_alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
	raw_name TEXT NOT NULL,
	tool_id INTEGER NOT NULL,
	FOREIGN KEY (tool_id) REFERENCES tool(tool_id)
	);
	