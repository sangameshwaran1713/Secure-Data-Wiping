"""
Compatibility shim for `eth_typing` provided at project root.

This module defers to the installed `eth_typing` package when available
but provides missing symbols (`ContractName`, `Manifest`) expected by
some downstream packages (e.g., web3/tools pytest helpers) so tests
and tools run without modifying the virtualenv site-packages.

Placing this package at the project root ensures it shadows the
site-packages `eth_typing` during test runs launched from the repo root.
"""
from typing import NewType

# Try to import the real package and re-export its public API
try:
    import importlib
    _real = importlib.import_module('eth_typing')
    # Import all public names from the real package into this namespace
    try:
        for name in getattr(_real, '__all__', []):
            globals()[name] = getattr(_real, name)
    except Exception:
        # Fallback: copy common attributes if available
        for attr in dir(_real):
            if not attr.startswith('_'):
                globals()[attr] = getattr(_real, attr)
except Exception:
    _real = None

# Provide compatibility NewTypes if missing
if not globals().get('ContractName'):
    ContractName = NewType('ContractName', str)

if not globals().get('Manifest'):
    Manifest = NewType('Manifest', dict)

# Provide HexStr and other common aliases expected by web3/eth-* packages
if not globals().get('HexStr'):
    HexStr = NewType('HexStr', str)

if not globals().get('ChecksumAddress'):
    ChecksumAddress = NewType('ChecksumAddress', str)

# Ensure ChainId is available by forwarding if present on real package
if _real is not None and not globals().get('ChainId'):
    ChainId = getattr(_real, 'ChainId', None)

# Minimal __all__ to satisfy imports
__all__ = [
    'ContractName',
    'Manifest',
]

# Add other exported names from the real package to __all__ if present
if _real is not None:
    try:
        __all__.extend([n for n in getattr(_real, '__all__', []) if n not in __all__])
    except Exception:
        pass


def __getattr__(name: str):
    """Fallback attribute access to the real `eth_typing` package when possible."""
    if _real is not None and hasattr(_real, name):
        return getattr(_real, name)
    raise AttributeError(f"module 'eth_typing' has no attribute '{name}'")


def __dir__():
    base = set(__all__)
    if _real is not None:
        try:
            base.update(getattr(_real, '__all__', []))
        except Exception:
            base.update([n for n in dir(_real) if not n.startswith('_')])
    return sorted(base)
