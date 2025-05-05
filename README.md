# 🧾 AI-Powered Invoice Processor

An intelligent, end-to-end document verification system for BFSI (Banking, Financial Services, and Insurance) applications. This Flask-based web app allows users to upload government-issued documents (like Aadhaar and PAN), which are then automatically validated using Google’s Generative AI (Gemini) and stored securely in a MySQL database. Email confirmations are also sent using SMTP.

---

## 🚀 Features

- ✅ Upload Aadhaar and PAN cards (PDF format)
- 🧠 AI-powered document verification using Gemini (Google Generative AI)
- 🔍 Extraction and validation of Aadhaar and PAN numbers
- 💾 Secure storage of user details in MySQL
- 📧 Automated email confirmations via SMTP
- 🌐 Flask-based user-friendly web interface

---

## 📂 Technologies Used

- **Frontend**: HTML/CSS wit React 
- **Backend**: Flask (Python)
- **AI Integration**: Google Generative AI (Gemini)
- **PDF Processing**: `pdfplumber`, `PyPDF2`
- **Database**: MySQL
- **Email Service**: SMTP
- **Vector Search (if used)**: FAISS
- **Text Processing**: LangChain (for splitting and handling large docs)

---
