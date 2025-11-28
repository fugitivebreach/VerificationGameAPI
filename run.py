"""
Startup script for VerificationAPI
"""

from api import app, init_database

if __name__ == '__main__':
    # Initialize the database
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")
    
    # Start the Flask server
    print("Starting VerificationAPI on http://0.0.0.0:5000")
    print("API Key: RoyalGuard20252026-API")
    app.run(host='0.0.0.0', port=5000, debug=True)
