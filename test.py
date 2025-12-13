
from document_reader import DocumentReader

target_folder = r"G:\My Drive\Personal\IIT\Deep Learning\Module 1"

reader = DocumentReader(target_folder)

documents = reader.read_all_documents()

first_doc = documents[0]

print()
print(first_doc['path'])
print()
print(first_doc['name'])
print()
print(first_doc['extension'])
print()
#print(first_doc['content'])
#print()
print(first_doc['relative_path'])

import json

with open("test_processes.json", "r") as f:
    process_flow = json.load(f)

from flow_database import FlowDatabase  # adjust import to match your file name

db = FlowDatabase("stream.db")

process_id = db.insert_multiple(process_flow)

print(f"Inserted process flow with ID {process_id}")

db.close()
