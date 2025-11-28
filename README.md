# VerificationAPI

A Flask-based REST API for managing Roblox-Discord verification data with SQLite database.

## Features

- **POST** - Create/Update verification data
- **GET** - Retrieve verification data by Roblox username
- **DELETE** - Remove verification data by Roblox username
- Automatic expiration checking and deletion
- API key authentication
- SQLite database storage

## API Key

```
RoyalGuard20252026-API
```

Include this in your requests as:
- Header: `X-API-Key: RoyalGuard20252026-API`
- Query parameter: `?api_key=RoyalGuard20252026-API`

## Installation

```bash
pip install -r requirements.txt
```

## Running the API

```bash
cd verification_api
python run.py
```

The API will start on `http://localhost:5000`

## Endpoints

### 1. POST `/api/verification`

Create or update verification data.

**Full Verification Request:**
```json
{
    "robloxUsername": "PlayerName",
    "robloxID": "123456789",
    "discordUsername": "User#1234",
    "discordID": "987654321",
    "timeToVerify": "1735689600",
    "joinedGame": false
}
```

**Update joinedGame Only:**
```json
{
    "robloxUsername": "PlayerName",
    "joinedGame": true
}
```

**Response (201 - Full Verification):**
```json
{
    "returnCode": 201,
    "response": "Verification data created/updated successfully",
    "robloxUsername": "PlayerName",
    "robloxID": "123456789",
    "discordUsername": "User#1234",
    "discordID": "987654321",
    "timeToVerify": "1735689600",
    "joinedGame": false
}
```

**Response (200 - joinedGame Update):**
```json
{
    "returnCode": 200,
    "response": "joinedGame updated successfully",
    "robloxUsername": "PlayerName",
    "joinedGame": true
}
```

### 2. GET `/api/verification/<robloxUsername>`

Retrieve verification data by Roblox username.

**Response (200):**
```json
{
    "returnCode": 200,
    "response": "Success",
    "robloxUsername": "PlayerName",
    "robloxID": "123456789",
    "discordUsername": "User#1234",
    "discordID": "987654321",
    "timeToVerify": "1735689600",
    "joinedGame": false
}
```

**Response (404) - Not found or expired:**
```json
{
    "returnCode": 404,
    "response": "Unable to fetch user details"
}
```

### 3. DELETE `/api/verification/<robloxUsername>`

Delete verification data by Roblox username.

**Response (200):**
```json
{
    "returnCode": 200,
    "response": "Verification data for PlayerName deleted successfully"
}
```

**Response (404):**
```json
{
    "returnCode": 404,
    "response": "Unable to fetch user details"
}
```

### 4. GET `/api/health`

Health check endpoint (no API key required).

**Response (200):**
```json
{
    "returnCode": 200,
    "response": "VerificationAPI is running",
    "status": "healthy"
}
```

## Luau Example (Roblox)

```lua
local HttpService = game:GetService("HttpService")

local API_URL = "http://your-server:5000/api/verification/"
local API_KEY = "RoyalGuard20252026-API"

-- Function to get verification data by Roblox username
local function getVerificationData(robloxUsername)
    local url = API_URL .. robloxUsername .. "?api_key=" .. API_KEY
    
    local success, response = pcall(function()
        return HttpService:GetAsync(url)
    end)
    
    if success then
        local data = HttpService:JSONDecode(response)
        
        if data.returnCode == 200 then
            print("User found!")
            print("Roblox ID:", data.robloxID)
            print("Discord Username:", data.discordUsername)
            print("Discord ID:", data.discordID)
            print("Joined Game:", data.joinedGame)
            return data
        elseif data.returnCode == 404 then
            print("Unable to fetch user details")
            return nil
        end
    else
        warn("Request failed:", response)
        return nil
    end
end

-- Function to update joinedGame status
local function updateJoinedGame(robloxUsername, hasJoined)
    local url = API_URL:sub(1, -2) .. "?api_key=" .. API_KEY
    local payload = {
        robloxUsername = robloxUsername,
        joinedGame = hasJoined
    }
    
    local success, response = pcall(function()
        return HttpService:PostAsync(
            url,
            HttpService:JSONEncode(payload),
            Enum.HttpContentType.ApplicationJson
        )
    end)
    
    if success then
        local data = HttpService:JSONDecode(response)
        if data.returnCode == 200 then
            print("joinedGame updated successfully!")
            return true
        end
    else
        warn("Update failed:", response)
    end
    return false
end

-- Example usage
local userData = getVerificationData("PlayerName")
if userData and not userData.joinedGame then
    -- Player joined the game, update the status
    updateJoinedGame("PlayerName", true)
end
```

## Python Example

```python
import requests

API_URL = "http://localhost:5000/api/verification"
API_KEY = "RoyalGuard20252026-API"
HEADERS = {"X-API-Key": API_KEY}

# POST - Create verification
data = {
    "robloxUsername": "PlayerName",
    "robloxID": "123456789",
    "discordUsername": "User#1234",
    "discordID": "987654321",
    "timeToVerify": "1735689600",
    "joinedGame": False
}
response = requests.post(f"{API_URL}", json=data, headers=HEADERS)
print(response.json())

# POST - Update joinedGame only
update_data = {
    "robloxUsername": "PlayerName",
    "joinedGame": True
}
response = requests.post(f"{API_URL}", json=update_data, headers=HEADERS)
print(response.json())

# GET - Retrieve verification
response = requests.get(f"{API_URL}/PlayerName", headers=HEADERS)
print(response.json())

# DELETE - Remove verification
response = requests.delete(f"{API_URL}/PlayerName", headers=HEADERS)
print(response.json())
```

## Time Format

The `timeToVerify` field accepts:
- **Unix timestamp** (seconds): `"1735689600"`
- **ISO 8601 format**: `"2025-01-01T00:00:00"`

When the current time exceeds `timeToVerify`, the verification is automatically deleted on the next GET request.

## Database

The API uses SQLite database stored at `verification_api/verification.db`.

**Schema:**
```sql
CREATE TABLE verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    robloxUsername TEXT UNIQUE NOT NULL,
    robloxID TEXT NOT NULL,
    discordUsername TEXT NOT NULL,
    discordID TEXT NOT NULL,
    timeToVerify TEXT NOT NULL,
    joinedGame INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Error Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (missing fields)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found (user not found or expired)
- `405` - Method Not Allowed
- `500` - Internal Server Error
