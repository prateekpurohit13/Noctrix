# Noctrix AI - Secure Document Cleansing and Analysis System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-18+-000000?style=for-the-badge&logo=next.js&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge&logo=databricks&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</div>

**Noctrix** is an advanced multi-agent AI system designed for intelligent document processing, security assessment, and automated data anonymization. Built with a modern tech stack, it combines OCR, NLP, and AI-powered analysis to process various document formats while maintaining the highest security standards.

## 🌟 Features

- **Multi-Format Document Processing**: Supports PDF, DOCX, XLSX, PPTX, images (PNG, JPG), and ZIP archives
- **AI-Powered Multi-Agent System**: 5-agent pipeline for comprehensive document analysis
  - Document Understanding Agent
  - Analysis Agent
  - Security Assessment Agent
  - Anonymization Agent
  - Reporting Agent
- **Advanced OCR**: Powered by PaddleOCR for accurate text extraction
- **RAG (Retrieval-Augmented Generation)**: ChromaDB vector database for intelligent context retrieval
- **Security-First Approach**: Encryption at rest, JWT authentication, RBAC, and audit logging
- **Modern Web Interface**: Next.js frontend with real-time progress tracking
- **RESTful API**: FastAPI backend with async support

## 🏗️ Architecture

```
┌─────────────────┐
│   Next.js UI    │  (Port 3000)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Backend│  (Port 8000)
└────────┬────────┘
         │
         ├──► Document Processor (OCR, DOM Creation)
         ├──► Multi-Agent System (5 AI Agents)
         ├──► RAG Service (ChromaDB)
         ├──► Security Layer (Encryption, Auth)
         └──► Database Layer (MongoDB, PostgreSQL)
```

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **Node.js 18+** and npm
- **Ollama** (for local LLM inference)
- **MongoDB** (local or cloud instance)
- **PostgreSQL** (local or cloud instance)
- **Git**

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/prateekpurohit13/Noctrix.git
cd Noctrix
```

### 2. Set Up Ollama Models

Install Ollama from [https://ollama.ai](https://ollama.ai), then pull the required models:

```bash
ollama pull llava
ollama pull mistral
ollama pull gemma:2b
```

### 3. Install Python Dependencies

In the root folder, install all required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Rename `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Or on Windows:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit the `.env` file and configure your values:
   ```env
   # Database Configuration
   MONGO_URI=mongodb+srv://your_username:your_password@cluster0.xxx.mongodb.net/
   MONGO_DB_NAME=noctrix_db
   
   POSTGRES_USER=your_postgres_user
   POSTGRES_PASSWORD=your_postgres_password
   POSTGRES_HOST=localhost
   POSTGRES_DB=noctrix_db
   POSTGRES_PORT=5432
   
   # Security Configuration
   KEK_BASE64=your_32_byte_base64_key
   ENCRYPTION_KEY=your_hex_string_here
   
   # JWT Configuration
   JWT_ISSUER=noctrix_ai_service
   JWT_AUDIENCE=noctrix_users
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7
   
   # Default Admin Credentials
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=Admin@12345
   ```

### 5. Set Up Frontend

Navigate to the `noctrix-ui` directory and install dependencies:

```bash
cd noctrix-ui
npm install
```

## 🎯 Running the Application

### Start the Backend (FastAPI)

From the **root directory** of the project:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Start the Frontend (Next.js)

Open a **new terminal**, navigate to the `noctrix-ui` directory, and run:

```bash
cd noctrix-ui
npm run dev
```

The web interface will be available at: `http://localhost:3000`

## 🛠️ Usage

### Using the Web Interface

1. Open your browser and navigate to `http://localhost:3000`
2. Log in with your admin credentials (configured in `.env`)
3. Upload documents through the web interface
4. Monitor real-time processing progress
5. View analysis reports and download anonymized documents

### Using the CLI (Command Line)

Process a single document using the multi-agent system:

```bash
python run_multi_agent.py data/input/your_document.pdf
```

Or use the document processor:

```bash
python run_processor.py data/input/your_document.xlsx
```

### Using the API

Example: Upload a document for processing

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

## 📁 Project Structure

```
Noctrix/
├── src/                          # Backend source code
│   ├── main.py                   # FastAPI application
│   ├── document_processor/       # OCR and DOM creation
│   ├── multi_agent_system/       # 5 AI agents
│   ├── rag/                      # RAG service (ChromaDB)
│   ├── security/                 # Encryption, auth, RBAC
│   ├── reporting/                # PDF/MD report generation
│   └── audit/                    # Audit logging
├── noctrix-ui/                   # Next.js frontend
│   ├── app/                      # Next.js app router pages
│   ├── components/               # React components
│   └── contexts/                 # React contexts
├── data/                         # Data directory
│   ├── input/                    # Input documents
│   └── output/                   # Processed output
├── vector_db/                    # ChromaDB storage
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## 🔒 Security Features

- **Encryption at Rest**: Sensitive data encrypted using AES
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control (RBAC)**: Fine-grained permissions
- **Audit Logging**: Complete audit trail for all operations
- **Secure File Handling**: Validated and sanitized inputs
- **Data Anonymization**: AI-powered PII detection and redaction

## 🤖 Multi-Agent System

The system employs 5 specialized AI agents:

1. **Document Understanding Agent**: Extracts structure and metadata
2. **Analysis Agent**: Performs deep content analysis
3. **Security Assessment Agent**: Identifies security risks and sensitive data
4. **Anonymization Agent**: Redacts PII and sensitive information
5. **Reporting Agent**: Generates comprehensive reports

## 🧪 Testing

Run tests with:

```bash
pytest
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 👨‍💻 Maintainer

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/prateekpurohit13">
        <img src="https://github.com/prateekpurohit13.png" width="100px;" alt="Prateek Purohit" style="border-radius: 50%;"/>
        <br />
        <sub><b>Prateek Purohit</b></sub>
      </a>
    </td>
  </tr>
</table>

## 👥 Collaborators

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/AKSHITAMODA">
        <img src="https://github.com/AKSHITAMODA.png" width="100px;" alt="Akshita Moda" style="border-radius: 50%;"/>
        <br />
        <sub><b>Akshita Moda</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/ANSHIKARAJ111">
        <img src="https://github.com/ANSHIKARAJ111.png" width="100px;" alt="Anshika Raj" style="border-radius: 50%;"/>
        <br />
        <sub><b>Anshika Raj</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/pratyushverma2005-debug">
        <img src="https://github.com/pratyushverma2005-debug.png" width="100px;" alt="Pratyush Verma" style="border-radius: 50%;"/>
        <br />
        <sub><b>Pratyush Verma</b></sub>
      </a>
    </td>
  </tr>
</table>

## 📄 License

<table>
  <tr>
    <td>
      <img src="https://upload.wikimedia.org/wikipedia/commons/0/0c/MIT_logo.svg" width="100px" alt="MIT License"/>
    </td>
    <td>
      This project is licensed under the <a href="LICENSE"><b>MIT License</b></a>. See the <a href="LICENSE">LICENSE</a> file for more details.
    </td>
  </tr>
</table>

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

<div align="center">

**Developed with ❤️ by Team <span style="color: #14b8a6;">Noctrix</span>**

</div>

---

**Note**: Ensure all environment variables are properly configured before running the application. Never commit your `.env` file to version control.
