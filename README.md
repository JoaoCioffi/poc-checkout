# poc-checkout

## ⚙️ Environment Setup

- First, create a python virtual environment at the root of this project. For example:

```bash
python3.11 -m venv .venv # '.venv' can be a different name
```

- Activate your venv:

```bash
# Linux:
. bin/activate

# Win
./.venv/Scripts/Activate.ps1
```

- Then, install dependencies:

```bash
pip install -r requirements.txt
```

- **IMPORTANT!** Make a copy of all `.env.ex` files and create a `.env` with the correct values before running anything

## 🐋 Docker

- Please, run

```bash
python run_service.py
```

## 📦 Streamlit

- You can run the streamlit as following:

```bash
streamlit run app.py --server.port 9000 # please choose a different port if needed
```
