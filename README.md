## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

1. **Clone or download the project**:
   ```bash
   cd data-viz-project
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```bash
     .venv\Scripts\activate.bat
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

With your virtual environment activated, run:

```bash
shiny run app.py
```

The app will start on `http://127.0.0.1:8000` (or similar). Open this URL in your web browser to view the dashboard.

### Auto-Reload Mode

To enable auto-reload when files change during development:

```bash
shiny run --reload app.py
```

## Data Files

The app requires two CSV data files in the `dataset/` directory:
- `1976-2020-president.csv` - Presidential election data
- `1976-2020-senate.csv` - Senate election data
