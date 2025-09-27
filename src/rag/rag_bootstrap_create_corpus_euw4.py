
import vertexai
from vertexai.preview import rag

vertexai.init(project="fresh-myth-471317-j9", location="europe-west4")

print("Listing corpora...")
for c in rag.list_corpora():
    print("FOUND:", c.name, c.display_name)

print("Creating corpus...")
corpus = rag.create_corpus(
    display_name="btai_rag_main_euw4",
    description="BrainTransplant-AI RAG corpus in europe-west4",
)
print("CREATED:", corpus.name)
