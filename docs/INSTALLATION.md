# Installation guide

## 1. Install Python

Use Python 3.10 or newer. During Windows installation, enable the option to add Python to PATH if the installer offers it. On macOS, install a current Python 3 release if `python3` is not already available. Check the installed version:

```powershell
py --version
```

On macOS or Linux:

```bash
python3 --version
```

## 2. Open the project folder

Open PowerShell/Terminal and change directory to the project root, where `requirements.txt` and `README.md` are located. In VS Code, use **File → Open Folder** to open that same root folder.

## 3. Create and activate a virtual environment

A virtual environment keeps this project's packages isolated from other projects.

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt instead:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

When active, the terminal prompt usually shows `(.venv)`. Activate the environment again whenever you open a new terminal for this project.

## 4. Install required libraries

With the environment active, run the command for your operating system:

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

On macOS/Linux:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The requirements include FastAPI and Uvicorn for the API, `httpx` for weather-provider requests, Pydantic for settings and validation, `python-dotenv` for local environment files, and Streamlit, Pandas, and Plotly for the dashboard.

## 5. Configure an API key safely

The current project uses Open-Meteo and does **not** require a weather API key. If you switch to a provider that requires one, create a private key in that provider's account and store it in a local `.env` file at the project root:

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
notepad .env
```

**macOS/Linux:**

```bash
cp .env.example .env
nano .env
```

Replace the placeholder with your own key, for example:

```dotenv
OPENWEATHER_API_KEY=put_your_private_key_here
```

Do not add quotes unless the provider's key format requires them. The API loads `.env` settings on startup using `python-dotenv`; the key should only be read by server-side provider code. Do not pass it to Streamlit/browser code, include it in a URL shown to users, or print it in logs. The current Open-Meteo service does not consume this optional setting; a provider adapter must be configured to use it when switching providers.

## 6. Verify the key stays out of GitHub

The root `.gitignore` excludes `.env` and other `.env.*` files while explicitly allowing `.env.example`. Before committing, check that Git ignores the private file:

```powershell
git check-ignore -v .env
git status --short
```

On macOS/Linux, use the same commands in Terminal. Confirm that `.env` is not listed as a file to commit and that `.env.example` contains only placeholders. Do not force-add `.env`. If a real key was committed or uploaded, revoke/rotate it with its provider immediately; deleting the file in a later commit does not make the exposed key secret again.

## 7. Start the application

Open two terminals in the project root and activate `.venv` in each.

**Terminal 1 — FastAPI:**

```powershell
py -m uvicorn main:app --reload
```

On macOS/Linux:

```bash
python -m uvicorn main:app --reload
```

**Terminal 2 — Streamlit dashboard:**

```powershell
py -m streamlit run src/dashboard/streamlit_app.py
```

On macOS/Linux:

```bash
python -m streamlit run src/dashboard/streamlit_app.py
```

Open the dashboard address printed in the terminal (usually `http://localhost:8501`). FastAPI docs are usually at `http://localhost:8000/docs`. Turn on **Simulation mode** to demonstrate the dashboard without external weather requests.

## 8. Deactivate the environment

When finished, run this in the terminal:

```text
deactivate
```

The `.venv` folder can be removed and recreated; it should not be uploaded to GitHub.
