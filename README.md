# 🧠 Transforming Text: An End-to-End NLP Pipeline with RAG

This project showcases a complete Retrieval-Augmented Generation (RAG) pipeline using **LLaMA 2 13B Chat**, **Pinecone**, and **LangChain** to perform intelligent document-based question answering.

It uses PDF-based datasets, embeds them into a vector space, stores them in Pinecone, and uses a local LLM for generating context-aware responses.

---

## 🚀 Features

- 📄 Load and parse PDFs using `PyMuPDF`
- 🧱 Chunk text and embed it using `sentence-transformers`
- 📦 Store embeddings in **Pinecone** for similarity search
- 💬 Use **LLaMA 2 (13B)** for local text generation with Hugging Face Transformers
- 🔍 Ask questions using LangChain’s `RetrievalQA` interface
- ✅ Works seamlessly with Google Colab + GPU

---

## 🧰 Tech Stack

- `LangChain`
- `sentence-transformers`
- `Pinecone`
- `Transformers` (LLaMA 2)
- `PyMuPDF`
- `Google Colab` (for mounting and storage)

---

## 🛠️ How to Use

1. **Install dependencies** (inside the notebook or requirements.txt)

2. **Mount Drive and Load PDFs**

   Place your `.pdf` files inside the `/content/drive/MyDrive/files/` folder.

3. **Set Pinecone API Key**

   ```python
   os.environ["PINECONE_API_KEY"] = "your-api-key"

4. **Set Hugging Face Auth Token**
```python
use_auth_token = "your-hf-token"
```

5. **Run the notebook or script**
Watch your PDFs turn into a fully searchable LLM-powered question-answer system!
