"""
Flask API for VerificationAPI - In-Memory Storage
"""

from flask import Flask, request, jsonify
from functools import wraps
from datetime import datetime

app = Flask(__name__)

# In-memory storage for verifications
# Structure: {roblox_username_lower: {"robloxUsername": str, "robloxID": str, "discordUsername": str, "discordID": str, "timeToVerify": str, "joinedGame": bool}}
verifications = {}

# API Key
API_KEY = "RoyalGuard20252026-API"


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if api_key != API_KEY:
            return jsonify({
                'returnCode': 401,
                'response': 'Unauthorized: Invalid API Key'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/verification', methods=['POST'])
@require_api_key
def create_verification():
    """
    POST endpoint to create/update verification data
    
    Expected JSON body:
    {
        "robloxUsername": "string",
        "robloxID": "string" (optional if updating joinedGame only),
        "discordUsername": "string" (optional if updating joinedGame only),
        "discordID": "string" (optional if updating joinedGame only),
        "timeToVerify": "string (ISO 8601 or Unix timestamp)" (optional if updating joinedGame only),
        "joinedGame": true/false (optional, defaults to false)
    }
    """
    try:
        data = request.get_json()
        
        # Check if this is a joinedGame-only update
        if 'joinedGame' in data and len(data) == 2 and 'robloxUsername' in data:
            username_lower = data['robloxUsername'].lower()
            
            if username_lower in verifications:
                verifications[username_lower]['joinedGame'] = data['joinedGame']
                return jsonify({
                    'returnCode': 200,
                    'response': 'joinedGame updated successfully',
                    'robloxUsername': data['robloxUsername'],
                    'joinedGame': data['joinedGame']
                }), 200
            else:
                return jsonify({
                    'returnCode': 404,
                    'response': 'Unable to fetch user details'
                }), 404
        
        # Validate required fields for full verification
        required_fields = ['robloxUsername', 'robloxID', 'discordUsername', 'discordID', 'timeToVerify']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'returnCode': 400,
                    'response': f'Missing required field: {field}'
                }), 400
        
        # Get joinedGame value (defaults to False)
        joined_game = data.get('joinedGame', False)
        
        # Store in memory
        username_lower = data['robloxUsername'].lower()
        verifications[username_lower] = {
            'robloxUsername': data['robloxUsername'],
            'robloxID': data['robloxID'],
            'discordUsername': data['discordUsername'],
            'discordID': data['discordID'],
            'timeToVerify': data['timeToVerify'],
            'joinedGame': joined_game
        }
        
        return jsonify({
            'returnCode': 201,
            'response': 'Verification data created/updated successfully',
            'robloxUsername': data['robloxUsername'],
            'robloxID': data['robloxID'],
            'discordUsername': data['discordUsername'],
            'discordID': data['discordID'],
            'timeToVerify': data['timeToVerify'],
            'joinedGame': joined_game
        }), 201
            
    except Exception as e:
        return jsonify({
            'returnCode': 500,
            'response': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/verification/<roblox_username>', methods=['GET'])
@require_api_key
def get_verification(roblox_username):
    """
    GET endpoint to retrieve verification data by Roblox username
    
    Returns 404 if user not found or verification expired
    """
    try:
        username_lower = roblox_username.lower()
        
        if username_lower not in verifications:
            return jsonify({
                'returnCode': 404,
                'response': 'Unable to fetch user details'
            }), 404
        
        verification = verifications[username_lower]
        
        # Check if verification has expired
        try:
            # Try parsing as Unix timestamp (seconds)
            expiry_time = datetime.fromtimestamp(float(verification['timeToVerify']))
        except (ValueError, TypeError):
            # Try parsing as ISO 8601
            try:
                expiry_time = datetime.fromisoformat(verification['timeToVerify'].replace('Z', '+00:00'))
            except:
                expiry_time = None
        
        if expiry_time and datetime.now() > expiry_time:
            # Delete expired verification
            del verifications[username_lower]
            return jsonify({
                'returnCode': 404,
                'response': 'Unable to fetch user details'
            }), 404
        
        # Return verification data
        return jsonify({
            'returnCode': 200,
            'response': 'Success',
            'robloxUsername': verification['robloxUsername'],
            'robloxID': verification['robloxID'],
            'discordUsername': verification['discordUsername'],
            'discordID': verification['discordID'],
            'timeToVerify': verification['timeToVerify'],
            'joinedGame': verification['joinedGame']
        }), 200
        
    except Exception as e:
        return jsonify({
            'returnCode': 500,
            'response': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/verification/<roblox_username>', methods=['DELETE'])
@require_api_key
def delete_verification(roblox_username):
    """
    DELETE endpoint to remove verification data by Roblox username
    """
    try:
        username_lower = roblox_username.lower()
        
        if username_lower in verifications:
            del verifications[username_lower]
            return jsonify({
                'returnCode': 200,
                'response': f'Verification data for {roblox_username} deleted successfully'
            }), 200
        else:
            return jsonify({
                'returnCode': 404,
                'response': 'Unable to fetch user details'
            }), 404
            
    except Exception as e:
        return jsonify({
            'returnCode': 500,
            'response': f'Internal server error: {str(e)}'
        }), 500


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'returnCode': 200,
        'response': 'VerificationAPI is running',
        'endpoints': [
            'GET /api/health',
            'POST /api/verification',
            'GET /api/verification/<username>',
            'DELETE /api/verification/<username>'
        ]
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint (no API key required)"""
    return jsonify({
        'returnCode': 200,
        'response': 'VerificationAPI is running',
        'status': 'healthy'
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'returnCode': 404,
        'response': 'Endpoint not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'returnCode': 405,
        'response': 'Method not allowed'
    }), 405


if __name__ == '__main__':
    import os
    # Run the Flask app (Railway provides PORT env variable)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
