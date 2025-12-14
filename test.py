
from document_reader import DocumentReader
from llm_extractor import FlowExtractor
from database import Database

target_folder = r"G:\My Drive\Projects\stream\test_data"

# Read all documents in the folder
reader = DocumentReader(target_folder)
documents = reader.read_all_documents()

# Instantiate the extractor
extractor = FlowExtractor(
    provider="ollama",
    model="llama2:7b",
    prompt_file="prompt_text.txt",
    max_tokens = 600
)

# Extract process flows from all documents
flows = extractor.extract_from_documents(documents)

# Print results
for flow in flows:
    print(f"Document: {flow['source_document']}")
    print(f"Process Name: {flow['process_name']}")
    print(f"Steps: {len(flow['steps'])}")
    print("---")

db = Database("stream.db")

process_id = db.insert_multiple(flows)

print(f"Inserted process flow with ID {process_id}")

db.close()
