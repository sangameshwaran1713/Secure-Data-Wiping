"""
Database Module

SQLite database management for local storage of wipe operations, blockchain records, and certificates.
"""

from .database_manager import DatabaseManager

__all__ = ['DatabaseManager']