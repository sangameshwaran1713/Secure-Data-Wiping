import json
import types
from verifier.app import app


class DummyReceipt:
    def __init__(self):
        self.transactionHash = bytes.fromhex('a'*64)
        self.status = 1
        self.blockNumber = 123
        self.gasUsed = 50000
        self.logs = []


class MockEth:
    chain_id = 1337
    block_number = 1
    accounts = ["0x0"]
    default_account = "0x0"

    @staticmethod
    def get_transaction_receipt(tx):
        return DummyReceipt()


class MockWeb3:
    def __init__(self, provider=None):
        self.eth = MockEth()

    def isConnected(self):
        return True


def test_health_endpoint():
    client = app.test_client()
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('status') == 'ok'


def test_verify_endpoint(monkeypatch):
    # Patch Web3 in verifier.app
    monkeypatch.setattr('verifier.app.Web3', MockWeb3)
    # ensure HTTPProvider exists
    MockWeb3.HTTPProvider = lambda url: url
    MockWeb3.toChecksumAddress = lambda x: x

    client = app.test_client()
    resp = client.get('/verify?tx=' + 'a'*64)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'transactionHash' in data
    assert data['status'] == 1
    