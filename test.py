

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
