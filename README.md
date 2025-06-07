# Orchids SWE Intern Challenge Template

This project consists of a backend built with FastAPI and a frontend built with Next.js and TypeScript.

## Backend

The backend uses uv for package management.

### Installation

To install the backend dependencies, run the following command in the backend project directory:

```
uv sync
```

Additionally, you must install Chromium for Playwright by running:

```
uv run playwright install chromium
```

### Ollama Setup (Local LLM)

This project uses Ollama to run an in-house language model locally.

#### Install Ollama

Download and install Ollama from [https://ollama.com/download](https://ollama.com/download)

#### Pull the model

By default, this app uses the llama3 model. Pull it with:

```
ollama pull llama3
```

#### Run the Ollama server

Start the local Ollama server with:

```
ollama serve
```

#### (Optional but recommended) Change model or port, I was limited to llama3 because my laptop is not the most powerful

If you use a different model or run Ollama on a different port, update the following lines in backend/app/llm.py:

```
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "llama3"
```

### Running the Backend

To start the backend development server, run:

```
uv run fastapi dev
```

## Frontend

The frontend is built with Next.js and TypeScript.

### Installation

Navigate to the frontend project directory and install dependencies with:

```
npm install
```

### Running the Frontend

To launch the frontend development server, run:

```
npm run dev
```
