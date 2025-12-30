"""STS Credential model
"""
from pydantic import BaseModel


class STSCredential(BaseModel):
    """STS Credential model
    """
    access_key_id: str
    access_key_secret: str
    security_token: str
    expiration: str
