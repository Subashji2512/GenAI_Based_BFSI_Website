from flask import Flask, request, jsonify, render_template
from PyPDF2 import PdfReader
import pdfplumber
import pytesseract
from PIL import Image
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def extract_text_from_image(image):
    print("text to image")
    return pytesseract.image_to_string(image)


def get_pdf_text(pdf_paths):
    print("get_pdf func")
    text = ""
    for pdf_path in pdf_paths:
        with pdfplumber.open(pdf_path) as pdf_reader:
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    # If no text, OCR the page as image
                    page_image = page.to_image()
                    ocr_text = extract_text_from_image(page_image.original)
                    text += ocr_text
    return text

def get_text_chunks(text):
    print("in text_chunks")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    You are a smart financial assistant specializing in analyzing bank statements. Use the provided context to answer the user's question clearly and concisely, including only the most relevant details.

Context:
{context}

Question:
{question}

Answer Guidelines:
If the answer is in the context:

Keep responses short and to the point.

For transaction-related queries:

Mention highest and lowest transactions (amount + brief description).

Include total spent last month, if relevant.

Only give savings tips if the user asks about savings or advice.

Recommend safe, traditional options (e.g., fixed deposits, gold, emergency funds).

Suggest basic habits (e.g., cut luxury spending) if overspending is visible.

Avoid investment advice in crypto, stocks, or unregulated assets.

If the answer is NOT in the context:

Say: "The answer is not in the provided context. However, here is some general information that may help:"

Then offer brief, relevant tips.

Encourage a follow-up question if needed.

When applicable, summarize briefly:
Highest transaction

Lowest transaction

Total spent last month

Add tips only if user asks for savings or advice
"""
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    response = chain.invoke({"input_documents": docs, "question": user_question})
    return response["output_text"]