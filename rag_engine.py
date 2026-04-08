import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

load_dotenv()

EMBED_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are WebsiteGPT. Answer ONLY using the WEBSITE CONTENT below. No outside knowledge ever.

STRICT RULES:
1. Only use information explicitly written in WEBSITE CONTENT. Never use training knowledge.
2. If the answer is not in the content, say exactly: "I couldn't find that on this website."
3. Never invent URLs, facts, or numbers. If you don't have a URL, don't write one.
4. Never say "likely", "probably", "implied", or "no URL provided".
5. Always state which page URL your answer came from.
6. For stats, numbers, tables — quote the exact text from the site.

WEBSITE CONTENT:
{context}

QUESTION: {question}

ANSWER:"""
)


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )


def build_vectorstore_from_docs(documents):
    """Returns (vectorstore, chunk_count)."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        separators=['\n\n', '\n', '. ', ' ', '']
    )
    chunks = splitter.split_documents(documents)
    print(f'Created {len(chunks)} chunks from {len(documents)} pages')
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(documents=chunks, embedding=embeddings)
    return vectorstore, len(chunks)


def get_qa_chain(vectorstore):
    llm = ChatGroq(
        model='llama-3.1-8b-instant',
        temperature=0,
        groq_api_key=os.getenv('GROQ_API_KEY')
    )
    memory = ConversationBufferWindowMemory(
        k=5,
        memory_key='chat_history',
        return_messages=True,
        output_key='answer'
    )
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(
            search_type='mmr',
            search_kwargs={
                'k': 5,
                'fetch_k': 20,
                'lambda_mult': 0.5
            }
        ),
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT}
    )