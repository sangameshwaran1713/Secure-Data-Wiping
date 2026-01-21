from flask import Flask, jsonify, request
from web3 import Web3
import os
import json

app = Flask(__name__)

# Configuration (environment overrides)
GANACHE_URL = os.environ.get("GANACHE_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS")
ABI_PATH = os.environ.get("CONTRACT_ABI_PATH", "config/contract_abi.json")


def load_abi(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/verify", methods=["GET"])
def verify():
    tx_hash = request.args.get("tx") or request.args.get("transaction")
    if not tx_hash:
        return jsonify({"error": "missing transaction hash (tx) parameter"}), 400

    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.isConnected():
        return jsonify({"error": "cannot connect to blockchain provider"}), 502

    # Normalize tx hash
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception as exc:
        return jsonify({"error": "transaction not found", "detail": str(exc)}), 404

    # Attempt to load contract ABI and decode logs (best-effort)
    abi = load_abi(ABI_PATH)
    decoded_events = []
    if abi and CONTRACT_ADDRESS:
        try:
            contract = w3.eth.contract(address=Web3.toChecksumAddress(CONTRACT_ADDRESS), abi=abi)
            for log in receipt.logs:
                try:
                    decoded = contract.events.WipeRecorded().processLog(log)
                    decoded_events.append(dict(decoded.args))
                except Exception:
                    # ignore logs that don't match
                    pass
        except Exception:
            pass

    response = {
        "transactionHash": receipt.transactionHash.hex(),
        "status": receipt.status,
        "blockNumber": receipt.blockNumber,
        "gasUsed": receipt.gasUsed,
        "decodedEvents": decoded_events,
    }

    return jsonify(response)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
