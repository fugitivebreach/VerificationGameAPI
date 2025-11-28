"""
VerificationAPI - A Flask-based API for managing Roblox-Discord verification data
"""

from .api import app, init_database

__all__ = ['app', 'init_database']
