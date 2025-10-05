
# 🤖 Intelligent WhatsApp Tutor

A sophisticated WhatsApp chatbot designed to help users find study materials and answer questions directly from them. This bot uses a **Retrieval-Augmented Generation (RAG)** architecture, leveraging Large Language Models (LLMs) via the OpenRouter API to provide intelligent, context-aware assistance.

## ✨ Key Features

  * **🧠 Natural Language Querying:** Users can search for resources using everyday language (e.g., "AI notes for module 3 by smith"). The bot uses `gpt-4o-mini` to understand the query and extract key details.
  * **📚 Resource Retrieval:** Efficiently filters a CSV database using Pandas to find matching study materials based on subject, faculty, module, semester, or subject code.
  * **💬 Interactive Q\&A:** After finding a document, users can enter a Q\&A mode to ask specific questions. The bot will answer based *only* on the content of the retrieved PDF(s).
  * **📄 PDF Text Extraction:** Uses `PyMuPDF` to read and process the text content of PDF documents for the Q\&A module.
  * **🤖 RAG-Powered Answers:** Employs `claude-3-haiku` to generate concise, exam-suitable answers strictly from the provided document text, preventing hallucinations and ensuring accuracy.
  * **🔄 State Management:** Maintains a simple user context to handle multi-turn conversations (e.g., switching between retrieval and Q\&A modes).
  * **🛠️ Tech Stack:** **Flask**, **Twilio API**, **OpenRouter API**, **Pandas**, **PyMuPDF**.

-----

## ⚙️ How It Works

The application follows a two-stage process: **Retrieval** and **Generation**.

1.  **Message Reception:** The Flask server receives an incoming WhatsApp message from a user via the Twilio webhook.
2.  **Intent Analysis (Query Parsing):**
      * The user's message is sent to an LLM (`gpt-4o-mini`) with a specialized system prompt.
      * The LLM extracts relevant entities (`subject`, `faculty`, `module`, etc.) and returns them as a structured JSON object.
3.  **Retrieval Phase:**
      * The application uses the extracted JSON to filter a Pandas DataFrame loaded from `rag-link - AIML.csv`.
      * If matching resources are found, their links are sent back to the user.
4.  **Generation Phase (Q\&A):**
      * The user can choose to ask questions about the found documents.
      * The bot extracts all text from the relevant local PDF files (`downloads/<id>.pdf`).
      * This extracted text (the "context") and the user's question are sent to a second LLM (`claude-3-haiku`).
      * The LLM generates an answer based *only* on the provided context and sends it to the user.

-----

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### 1\. Prerequisites

  * Python 3.8+
  * [ngrok](https://www.google.com/search?q=https://ngrok.com/download) to expose your local server to the internet.
  * A Twilio account with a configured WhatsApp Sandbox.
  * An OpenRouter API key.

### 2\. Installation

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    *(You will need to create a `requirements.txt` file, see below)*

### 3\. Configuration

1.  **Create a `requirements.txt` file** in the root directory with the following content:

    ```
    flask
    pandas
    requests
    twilio
    PyMuPDF
    ```

2.  **Create a `.env` file** in the root directory to store your secret keys. **Do not hardcode keys in your Python script.**

    ```
    # --- OpenRouter Configuration ---
    OPENROUTER_API_KEY="sk-or-v1-your-openrouter-api-key"

    # --- Twilio Configuration ---
    ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    AUTH_TOKEN="your_twilio_auth_token"
    FROM_NUMBER="whatsapp:+14155238886" # Your Twilio WhatsApp Number
    ```

    *You'll need to modify your Python script to load these variables using a library like `python-dotenv`.*

3.  **Prepare your data:**

      * Create a CSV file named `rag-link - AIML.csv` in the root directory with columns like: `subject`, `faculty`, `subject-code`, `semester`, `module`, `resource-link`, and `id`.
      * Create a folder named `downloads`.
      * Place your PDF files inside `downloads`, ensuring each file is named `<id>.pdf` to match the `id` column in your CSV.

### 4\. Running the Application

1.  **Start the Flask server:**

    ```bash
    python app.py
    ```

    Your server will be running on `http://127.0.0.1:5000`.

2.  **Expose your local server using ngrok:**

    ```bash
    ngrok http 5000
    ```

    ngrok will give you a public URL (e.g., `https://random-string.ngrok.io`).

3.  **Configure the Twilio Webhook:**

      * Go to your Twilio Console -\> Messaging -\> Senders -\> WhatsApp Senders.
      * Select your sandbox number.
      * Under "Webhook URL for incoming messages", paste your ngrok URL followed by `/whatsapp` (e.g., `https://random-string.ngrok.io/whatsapp`).
      * Set the method to `HTTP POST`.
      * Save the configuration.

### 5\. Usage

You can now send messages to your Twilio WhatsApp number and interact with the bot\!

**Example Queries:**

  * `notes for artificial intelligence`
  * `BCS515C module 4 notes`
  * `send me the notes from the fifth semester`

After getting a result, reply with `1` to start asking questions about the document.

-----

## 💡 Future Improvements

  * **Database Integration:** Replace the CSV file with a robust database like PostgreSQL or SQLite for better scalability and data management.
  * **Asynchronous Processing:** Use Celery or a similar task queue to handle LLM API calls and PDF processing asynchronously, preventing webhook timeouts.
  * **Advanced State Management:** Implement a more persistent session management solution (e.g., using Redis or Flask-Session) instead of an in-memory dictionary.
  * **Error Handling:** Enhance error logging and provide more descriptive error messages to the user.

-----

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
