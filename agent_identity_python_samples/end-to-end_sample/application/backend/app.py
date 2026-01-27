import json
import uuid
import httpx
import traceback
import jwt
import hashlib
import base64
from typing import Dict, Any, List, Optional

from agent_identity_python_sdk.core import IdentityClient
from agent_identity_python_sdk.core.decorators import get_region
from agent_identity_python_sdk.utils.config import read_local_config
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

import sys
import os
import logging

from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from .config import get_app_config_with_default

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production environment, specific domains should be specified
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


redirect_uri = get_app_config_with_default('INBOUND_REDIRECT_URI', '')
identity_client = IdentityClient(region_id=get_region())

# User token mapping
user_token_map: Dict[str, str] = {}
user_session_map: Dict[str, str] = {}
pkce_challenge_map: Dict[str, str] = {}

class ChatRequest(BaseModel):
    """
    Chat request model
    """
    input: List[Dict[str, Any]]
    session_id: Optional[str]

class AgentRequest(BaseModel):
    """
    Agent request model
    """
    input: List[Dict[str, Any]]
    session_id: Optional[str]
    user_id: Optional[str]

class OAuthCallbackRequest(BaseModel):
    """
    OAuth callback request model
    """
    code: str
    state: Optional[str] = None

@app.get("/health")
async def health_check():
    """
    Health check interface
    """
    return {"status": "healthy"}

@app.post("/chat")
async def chat(
    chat_request: ChatRequest,
    session_id: Optional[str] = Header(None, alias="session-id")
):
    """
    Chat interface - Provides streamable HTTP connection for frontend calls
    Calls the process interface of the main service via streamable HTTP
    
    Args:
        chat_request (ChatRequest): Chat request data
        session_id (Optional[str]): Session ID from header
        
    Returns:
        StreamingResponse: Stream response from main service
        
    Raises:
        HTTPException: When user is not logged in or other errors occur
    """
    try:
        logger.info(f"Received session_id from header: {session_id}")
        chat_session_id = chat_request.session_id or str(uuid.uuid4())
        if chat_session_id not in user_session_map:
            user_session_map[chat_session_id] = session_id

        # Check if user is logged in
        if session_id not in user_token_map:
            logger.warning(f"Session {session_id} not found in oauth_tokens")
            raise HTTPException(status_code=401, detail="User not logged in")

        # Get user information from oauth_tokens
        id_token = user_token_map.get(session_id)
        logger.info(f"Token data for session: {id_token}")
        if not id_token:
            raise HTTPException(status_code=401, detail="Invalid session")

        # Return streaming response
        return StreamingResponse(
            forward_to_main_service(agent_request=AgentRequest(
                input=chat_request.input,
                session_id=chat_session_id,
                user_id=id_token
            )),
            media_type="text/event-stream"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_details = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        logger.error(f"Chat endpoint error: {error_details}")
        raise HTTPException(status_code=500, detail=error_details)

async def forward_to_main_service(agent_request: AgentRequest):
    """
    Forward request to the process interface of the main service
    
    Args:
        agent_request (AgentRequest): Agent request data
        
    Yields:
        bytes: Response chunks from main service
    """
    try:
        # Construct request data, keeping consistent with agent interface in main.py
        request_data = {
            "messages": agent_request.input,
            "session_id": agent_request.session_id,
            "user_id": agent_request.user_id,
            "stream": 'true'
        }
        
        logger.info(f"Forwarding request to main service: {request_data}")
        
        # Send POST request to main service
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream(
                "POST", 
                get_app_config_with_default("AGENT_ENDPOINT", "http://localhost:8080/process"),
                json=request_data,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + get_app_config_with_default("AGENT_BEARER_TOKEN", "MOCK"),
                         }
            ) as response:
                logger.info(f"Received response from main service. Status: {response.status_code}")
                
                # Read and forward streaming response
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk
                        logger.info(f"Forwarded chunk to client: {chunk}")
                        
                        # Check for end marker
                        try:
                            # If chunk is plain text data (starting with data:)
                            if chunk.startswith(b'data:'):
                                data_str = chunk.decode('utf-8').strip()
                                if data_str.startswith('data:'):
                                    json_part = data_str[5:].strip()  # Remove "data:" prefix
                                    if json_part:
                                        data_obj = json.loads(json_part)
                                        # Check for completion status object
                                        if data_obj.get('status') == 'completed' and data_obj.get('type') == 'text' and 'message' in data_obj.get('object', ''):
                                            logger.info("Detected completion message, ending stream")
                                            break
                            # If chunk is JSON itself (without data: prefix)
                            else:
                                data_obj = json.loads(chunk.decode('utf-8'))
                                if data_obj.get('status') == 'completed' and data_obj.get('type') == 'text' and 'message' in data_obj.get('object', ''):
                                    logger.info("Detected completion message, ending stream")
                                    break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # If not valid JSON, continue processing next chunk
                            pass
                    
    except httpx.ConnectError as e:
        error_message = {
            "error": f"Cannot connect to main service: {str(e)}",
            "type": "ConnectError",
            "details": str(e)
        }
        logger.error(f"Connection error: {error_message}")
        yield json.dumps(error_message).encode('utf-8')
    except httpx.TimeoutException as e:
        error_message = {
            "error": f"Request timeout: {str(e)}",
            "type": "TimeoutException",
            "details": str(e)
        }
        logger.error(f"Timeout error: {error_message}")
        yield json.dumps(error_message).encode('utf-8')
    except Exception as e:
        error_details = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        logger.error(f"Forwarding error: {error_details}")
        yield json.dumps(error_details).encode('utf-8')
    
    # End signal
    yield b"\n\n[DONE]"

@app.post("/callback_for_oauth")
async def callback_for_oauth(request: OAuthCallbackRequest):
    """
    OAuth callback endpoint - Receives authorization code and calls Aliyun OAuth token interface
    
    Args:
        request (OAuthCallbackRequest): OAuth callback request containing authorization code
        
    Returns:
        JSONResponse: Response containing session ID and user ID
        
    Raises:
        HTTPException: When OAuth configuration is incomplete or token retrieval fails
    """
    try:
        # Get OAuth configuration
        client_id = read_local_config('inbound_app_id') or get_app_config_with_default("INBOUND_APP_ID", None)

        # Check if necessary configurations exist
        if not all([client_id, redirect_uri]):
            raise HTTPException(status_code=500, detail="OAuth configuration is incomplete, please check config.json")

        # Construct request data
        data = {
            'code': request.code,
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'code_verifier': pkce_challenge_map[request.state],
        }
        
        logger.info(f"Calling OAuth token endpoint with data: {data}")
        
        # Call Aliyun OAuth token interface
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://oauth.aliyun.com/v1/token',
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Check response status
            if response.status_code == 200:
                token_data = response.json()
                logger.info(f"Successfully obtained token: {token_data}")
                
                # Generate random session ID
                session_id = str(uuid.uuid4())
                
                # Parse id_token to get sub
                id_token = token_data.get('id_token')
                user_token_map[session_id] = id_token
                sub = None
                if id_token:
                    try:
                        # Decode JWT token (without signature verification)
                        decoded = jwt.decode(id_token, options={"verify_signature": False})
                        sub = decoded.get('sub')
                    except Exception as e:
                        logger.error(f"Failed to decode id_token: {e}")
            
                # Create response and return data (frontend is responsible for storage)
                response_data = {
                    "session_id": session_id,
                    "user_id": sub
                }
                
                return JSONResponse(content=response_data)
            else:
                error_detail = {
                    "status_code": response.status_code,
                    "response": response.text
                }
                logger.error(f"Failed to obtain token: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=error_detail)
                
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_details = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        logger.error(f"OAuth callback error: {error_details}")
        raise HTTPException(status_code=500, detail=error_details)


@app.get("/callback")
async def callback(session_uri: str, state: str, request: Request):
    """
    Callback interface - Handles authentication callback
    
    Args:

        session_uri (str): Session URI returned by Agent Identity callback, used for client confirmation when obtaining OAuth Token

        state (str): State parameter, which is the chat session ID passed through by the backend service to the Agent. 
                     When the Agent Identity callbacks to the backend service, it's recommended to verify 
                     the state against the caller's identity (usually stored in cookies) to ensure 
                     the OAuth authorizer and initiator are the same user.
        request (Request): HTTP request object
        
    Returns:
        str: Success message
        
    Raises:
        HTTPException: When login session ID is missing or invalid
    """
    # Get login_session_id from cookies
    login_session_id = request.cookies.get("oauthSessionId")
    
    # Check if login_session_id exists
    if not login_session_id:
        raise HTTPException(status_code=400, detail="Missing login_session_id cookie")


    # Check if the state (i.e., the chat session ID passed in when initiating chat) exists
    # Need to verify that its corresponding login session ID matches the session ID in the current caller's cookie
    # Otherwise, the authorization link may have been forwarded to someone else, in which case confirmation should be denied
    if user_session_map.get(state) is None:
        raise HTTPException(status_code=400, detail="Invalid state")

    state_session_id = user_session_map[state]
    if state_session_id != login_session_id:
        raise HTTPException(status_code=400, detail="Invalid login_session_id")

    try:
        identity_client.confirm_user_auth(session_uri=session_uri, user_token=user_token_map[state_session_id])
    except Exception as e:
        logger.error(e)
        raise e

    return HTMLResponse(content="""
    <html>
    <head>
        <title>Success</title>
        <script>
            setTimeout(function() {
                window.close();
            }, 3000);
        </script>
    </head>
    <body>
        <h1>Success</h1>
        <p>This window will close automatically in 3 seconds.</p>
    </body>
    </html>
    """, status_code=200)

@app.get("/auth")
async def auth():
    """
    Auth endpoint - Returns an authorization link
    
    Returns:
        str: Authorization link
    """
    client_id = read_local_config('inbound_app_id') or get_app_config_with_default("INBOUND_APP_ID", None)

    code_verifier = f"agent-identity-sample-pkce-verifier-{uuid.uuid4().__str__()}"
    state = uuid.uuid4().__str__()
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().replace("=", "")
    pkce_challenge_map[state] = code_verifier

    auth_url = f"https://signin.aliyun.com/oauth2/v1/auth?client_id={client_id}&redirect_uri={redirect_uri}&state={state}&code_challenge={code_challenge}&code_challenge_method=S256&response_type=code"
    return auth_url


app.mount("/", StaticFiles(directory="application/frontend/dist", html=True))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)