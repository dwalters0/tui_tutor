#import pymupdf
from pathlib import Path

# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
# from llama_index.embeddings.openai_like import OpenAILikeEmbedding
# from llama_index.core import StorageContext, load_index_from_storage
# from llama_index.core.ingestion import IngestionPipeline
# from llama_index.core.node_parser import SentenceSplitter

from configuration import get_config

#singleton retriever
_retriever = None

def get_retriever(persist_dir,top_k=5):
    raise NotImplementedError
    global _retriever
    
    print(f"Getting retriever for {persist_dir}")
    
    if _retriever is None:
        config = get_config()

        embed_model = OpenAILikeEmbedding(
            api_base=config.rag_retrieval_url,
            api_key=config.rag_retrieval_authorization,  # often ignored by local servers
            model_name=config.rag_model,
            #be good if this worked, maybe experiment with it more
            # additional_kwargs={
        #     "options": {
        #         "num_gpu": 0
        #     }
        # }
        )

        #llamaindex settings, had to set this
        Settings.embed_model = embed_model

        print("Loading retriever...")
        storage_context = StorageContext.from_defaults(
            persist_dir=persist_dir
        )
        index = load_index_from_storage(storage_context)
        _retriever = index.as_retriever(similarity_top_k=top_k)

    return _retriever

def get_rag_context(persist_dir, question, delimiter="\n\nREFERENCE:"):
    raise NotImplementedError
    retriever = get_retriever(persist_dir)
    nodes = retriever.retrieve(question)
    rag_context = delimiter.join(node.text for node in nodes)
    return rag_context

def reset_retriever():
    raise NotImplementedError
    global _retriever
    _retriever = None

def clear_textbooks():
    reset_retriever()

def convert_pdf_to_text(pdf_path, output_path):
    raise NotImplementedError
    # PyMuPDF
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


def create_rag_storage(source_path,persist_dir):
    raise NotImplementedError
    config = get_config()
    embed_model = OpenAILikeEmbedding(
        api_base=config.rag_embedding_url,
        api_key=config.rag_embedding_authorization,  # often ignored by local servers
        model_name=config.rag_model,
    )

    #llamaindex settings, had to set this
    Settings.embed_model = embed_model

    # create the pipeline with transformations
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=128, chunk_overlap=64),
            OpenAILikeEmbedding(api_base=config.rag_embedding_url,
                                api_key=config.rag_embedding_authorization,
                                model_name=config.rag_model),
        ]
    )
    print("This will take a while...")
    documents = SimpleDirectoryReader(source_path).load_data()
    # run the pipeline
    print("Still Working [x][ ][ ][ ]")
    nodes = pipeline.run(documents=documents)
    print("Still Working [x][x][ ][ ]")
    index = VectorStoreIndex(nodes=nodes)
    print("Still Working [x][x][x][ ]")
    index.storage_context.persist(persist_dir)
    print("Done! [X][X][X][X]")