# -*- coding: utf-8 -*-
"""Rag_updated.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/18BDQQzMEcO6tuefcDRHcXOGRAmA8JaSW

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pinecone-io/examples/blob/master/learn/generation/llm-field-guide/llama-2/llama-2-13b-retrievalqa.ipynb) [![Open nbviewer](https://raw.githubusercontent.com/pinecone-io/examples/master/assets/nbviewer-shield.svg)](https://nbviewer.org/github/pinecone-io/examples/blob/master/learn/generation/llm-field-guide/llama-2/llama-2-13b-retrievalqa.ipynb)

# RAG with LLaMa 13B

In this notebook we'll explore how we can use the open source **Llama-13b-chat** model in both Hugging Face transformers and LangChain.
At the time of writing, you must first request access to Llama 2 models via [this form](https://ai.meta.com/resources/models-and-libraries/llama-downloads/) (access is typically granted within a few hours). If you need guidance on getting access please refer to the beginning of this [article](https://www.pinecone.io/learn/llama-2/) or [video](https://youtu.be/6iHVJyX2e50?t=175).

---

🚨 _Note that running this on CPU is sloooow. If running on Google Colab you can avoid this by going to **Runtime > Change runtime type > Hardware accelerator > GPU > GPU type > T4**. This should be included within the free tier of Colab._

---

We start by doing a `pip install` of all required libraries.
"""

# import locale
# locale.getpreferredencoding = lambda: "UTF-8"

!pip install -qU \
  transformers==4.31.0 \
  sentence-transformers==2.2.2 \
  pinecone-client==3.1.0 \
  datasets==2.14.0 \
  accelerate==0.26.0 \
  einops==0.6.1 \
  langchain==0.1.2 \
  xformers==0.0.20 \
  bitsandbytes==0.41.0 \
  langchain_pinecone \
  pymupdf

"""## Initializing the Hugging Face Embedding Pipeline

We begin by initializing the embedding pipeline that will handle the transformation of our docs into vector embeddings. We will use the `sentence-transformers/all-MiniLM-L6-v2` model for embedding.
"""

# Install necessary packages
!pip install --upgrade sentence-transformers huggingface_hub

# Ensure you restart your runtime after running this install block if in Jupyter/Colab

from torch import cuda
from langchain.embeddings.huggingface import HuggingFaceEmbeddings

# Define the embedding model ID
embed_model_id = 'sentence-transformers/all-MiniLM-L6-v2'

# Check if CUDA (GPU) is available and set the device
device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

# Initialize HuggingFace Embeddings
embed_model = HuggingFaceEmbeddings(
    model_name=embed_model_id,
    model_kwargs={'device': device},
    encode_kwargs={'device': device, 'batch_size': 32}  # Adjust batch_size if necessary
)

# Test the embedding model
text = ["Hello world", "How are you?"]
embeddings = embed_model.embed_documents(text)

# Print the embeddings
print("Embeddings generated successfully:")
print(embeddings)

from torch import cuda
from langchain.embeddings.huggingface import HuggingFaceEmbeddings

embed_model_id = 'sentence-transformers/all-MiniLM-L6-v2'

device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

embed_model = HuggingFaceEmbeddings(
    model_name=embed_model_id,
    model_kwargs={'device': device},
    encode_kwargs={'device': device, 'batch_size': 32}
)

"""We can use the embedding model to create document embeddings like so:"""

docs = [
    "this is one document",
    "and another document"
]

embeddings = embed_model.embed_documents(docs)

print(f"We have {len(embeddings)} doc embeddings, each with "
      f"a dimensionality of {len(embeddings[0])}.")

"""## Building the Vector Index

We now need to use the embedding pipeline to build our embeddings and store them in a Pinecone vector index. To begin we'll initialize our index, for this we'll need a [free Pinecone API key](https://app.pinecone.io/).
"""

import os
from pinecone import Pinecone

# initialize connection to pinecone (get API key at app.pinecone.io)
api_key = os.environ.get('PINECONE_API_KEY') or 'pcsk_62Mnjn_GCuTN5Co57RMCNtBZ4uUHy1NAEuBvPG2Bus4d5stu7fsewBnCsxBWz39Q8F86Qn'

# configure client
pc = Pinecone(api_key=api_key)

"""Now we setup our index specification, this allows us to define the cloud provider and region where we want to deploy our index. You can find a list of all [available providers and regions here](https://docs.pinecone.io/docs/projects)."""

from pinecone import ServerlessSpec

cloud = os.environ.get('PINECONE_CLOUD') or 'aws'
region = os.environ.get('PINECONE_REGION') or 'us-east-1'

spec = ServerlessSpec(cloud=cloud, region=region)

"""Now we initialize the index."""

index_name = 'llama-3-rag-test2'

import time

# check if index already exists (it shouldn't if this is first time)
if index_name not in pc.list_indexes().names():
    # if does not exist, create index
    pc.create_index(
        index_name,
        dimension=len(embeddings[0]),
        metric='cosine',
        spec=spec
    )
    # wait for index to be initialized
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)

# connect to index
index = pc.Index(index_name)
# view index stats
index.describe_index_stats()

"""With our index and embedding process ready we can move onto the indexing process itself. For that, we'll need a dataset. We will use a set of Arxiv papers related to (and including) the Llama 2 research paper."""

# from datasets import load_dataset

# data = load_dataset(
#     'jamescalam/llama-2-arxiv-papers-chunked',
#     split='train'
# )
# data

from langchain.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from google.colab import drive

drive.mount('/content/drive')

DATA_PATH = '/content/drive/MyDrive/files/'

def load_documents():
    loader = DirectoryLoader(DATA_PATH,  glob=f"**/*{'.pdf'}", show_progress=True, loader_cls=PyMuPDFLoader)
    documents = loader.load()
    return documents


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    # print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    document = chunks[10]
    # print(document.page_content)
    # print(document.metadata)

    return chunks

documents = load_documents()
chunks = split_text(documents)
print(chunks[0])

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
data = pd.DataFrame(columns=['page_content', 'metadata', 'type'])
for i in range(len(chunks)):
    data.loc[-1] = [chunks[i].page_content, chunks[i].metadata, chunks[i].type]
    data.index = data.index + 1
    data = data.sort_index()

data

"""We will embed and index the documents like so:"""

batch_size = 32

for i in range(0, len(data), batch_size):
    i_end = min(len(data), i+batch_size)
    batch = data.iloc[i:i_end]
    ids = [f"{i}" for i, x in batch.iterrows()]
    texts = [x['page_content'] for i, x in batch.iterrows()]
    embeds = embed_model.embed_documents(texts)
    # get metadata to store in Pinecone
    metadata = [
        {'text': x['page_content'],
         'source': x['metadata']['source'],
         'title': x['metadata']['title']} for i, x in batch.iterrows()
    ]
    # print(embeds)
    # add to Pinecone
    index.upsert(vectors=zip(ids, embeds, metadata))
    # print(ids)

index.describe_index_stats()

"""## Initializing the Hugging Face Pipeline

The first thing we need to do is initialize a `text-generation` pipeline with Hugging Face transformers. The Pipeline requires three things that we must initialize first, those are:

* A LLM, in this case it will be `meta-llama/Llama-2-13b-chat-hf`.

* The respective tokenizer for the model.

We'll explain these as we get to them, let's begin with our model.

We initialize the model and move it to our CUDA-enabled GPU. Using Colab this can take 5-10 minutes to download and initialize the model.
"""

from torch import cuda, bfloat16
import transformers

model_id = 'meta-llama/Llama-2-13b-chat-hf'

device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

# set quantization configuration to load large model with less GPU memory
# this requires the `bitsandbytes` library
bnb_config = transformers.BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=bfloat16
)

# begin initializing HF items, need auth token for these
hf_auth = 'your API key'
model_config = transformers.AutoConfig.from_pretrained(
    model_id,
    use_auth_token=hf_auth
)

model = transformers.AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    config=model_config,
    quantization_config=bnb_config,
    device_map='auto',
    use_auth_token=hf_auth
)
model.eval()
print(f"Model loaded on {device}")

"""The pipeline requires a tokenizer which handles the translation of human readable plaintext to LLM readable token IDs. The Llama 2 13B models were trained using the Llama 2 13B tokenizer, which we initialize like so:"""

tokenizer = transformers.AutoTokenizer.from_pretrained(
    model_id,
    use_auth_token=hf_auth
)

"""Now we're ready to initialize the HF pipeline. There are a few additional parameters that we must define here. Comments explaining these have been included in the code."""

generate_text = transformers.pipeline(
    model=model, tokenizer=tokenizer,
    return_full_text=True,  # langchain expects the full text
    task='text-generation',
    # we pass model parameters here too
    temperature=1.0,  # 'randomness' of outputs, 0.0 is the min and 1.0 the max
    max_new_tokens=512,  # mex number of tokens to generate in the output
    repetition_penalty=1.1  # without this output begins repeating
)

"""Confirm this is working:"""

res = generate_text("What is the full form of RTOR?")
print(res[0]["generated_text"])

"""Now to implement this in LangChain"""

from langchain.llms import HuggingFacePipeline

llm = HuggingFacePipeline(pipeline=generate_text)

llm(prompt="What is the full form of RTOR?")

"""We still get the same output as we're not really doing anything differently here, but we have now added **Llama 2 13B Chat** to the LangChain library. Using this we can now begin using LangChain's advanced agent tooling, chains, etc, with **Llama 2**.

## Initializing a RetrievalQA Chain

For **R**etrieval **A**ugmented **G**eneration (RAG) in LangChain we need to initialize either a `RetrievalQA` or `RetrievalQAWithSourcesChain` object. For both of these we need an `llm` (which we have initialized) and a Pinecone index — but initialized within a LangChain vector store object.

Let's begin by initializing the LangChain vector store, we do it like so:
"""

# !pip install langchain-pinecone

from langchain_pinecone import PineconeVectorStore

text_field = 'text'  # field in metadata that contains text content

vectorstore = PineconeVectorStore(
    index=index, embedding=embed_model, text_key=text_field
)

"""We can confirm this works like so:"""

query = 'What is the full form of RTOR?'

vectorstore.similarity_search(query)

"""Looks good! Now we can put our `vectorstore` and `llm` together to create our RAG pipeline."""

from langchain.chains import RetrievalQA

rag_pipeline = RetrievalQA.from_chain_type(
    llm=llm, chain_type='stuff',
    retriever=vectorstore.as_retriever()
)

"""Let's begin asking questions! First let's try *without* RAG:"""

llm('What is the full form of RTOR?')

"""Hmm, that's not what we meant... What if we use our RAG pipeline?"""

rag_pipeline('What is the full form of RTOR?')

"""This looks *much* better! Let's try some more."""