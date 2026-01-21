Minimal verifier service

This folder contains a small Flask app (`app.py`) that accepts a `tx` query parameter and returns a JSON summary of the transaction receipt and any decoded `WipeRecorded` events if the contract ABI and address are provided.

Quick start (local):

```bash
# from repository root
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install flask

# set environment variables (optional)
set CONTRACT_ADDRESS=0x... 
set CONTRACT_ABI_PATH=config/contract_abi.json

# run verifier
python verifier/app.py
```

Endpoints:
- `GET /health` — health check
- `GET /verify?tx=<txhash>` — verify a transaction and return decoded events
