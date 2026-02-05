"""
Utilities for Stacks wallet authentication
"""
import hashlib
import base64
from typing import Optional


def verify_stacks_signature(address: str, message: str, signature: str) -> bool:
    """
    Verify a Stacks wallet signature
    
    Args:
        address: Stacks wallet address (ST...)
        message: Original message that was signed
        signature: Hex-encoded signature from wallet
        
    Returns:
        bool: True if signature is valid
    """
    try:
        # For now, we'll implement basic validation
        # In production, you'd use stacks.js verification or similar
        
        # Basic checks
        if not address or not message or not signature:
            return False
        
        if not address.startswith('ST') and not address.startswith('SP'):
            return False
            
        # TODO: Implement actual signature verification using stacks-blockchain library
        # For development/testing, we can verify format only
        # In production, integrate with Stacks.js or similar for full verification
        
        # Signature should be a valid hex string
        try:
            bytes.fromhex(signature.replace('0x', ''))
        except ValueError:
            return False
        
        # For development: Accept valid format
        # TODO: Implement cryptographic verification
        return len(signature) > 64  # Basic length check
        
    except Exception as e:
        print(f"Signature verification error: {e}")
        return False


def generate_auth_message(action: str, timestamp: Optional[int] = None, nonce: Optional[str] = None) -> str:
    """
    Generate a standard message format for wallet signing
    
    Args:
        action: 'register' or 'login'
        timestamp: Unix timestamp (optional)
        nonce: Random nonce (optional)
        
    Returns:
        Formatted message string
    """
    import time
    
    if timestamp is None:
        timestamp = int(time.time())
    
    if nonce is None:
        import secrets
        nonce = secrets.token_hex(16)
    
    return f"""Domain: deorganized.app
Action: {action}
Timestamp: {timestamp}
Nonce: {nonce}"""


def validate_message_freshness(message: str, max_age_seconds: int = 300) -> bool:
    """
    Validate that a signed message is recent (within max_age_seconds)
    
    Args:
        message: The signed message
        max_age_seconds: Maximum age in seconds (default: 5 minutes)
        
    Returns:
        bool: True if message is fresh
    """
    import time
    
    try:
        # Extract timestamp from message
        for line in message.split('\n'):
            if line.startswith('Timestamp:'):
                timestamp_str = line.split(':', 1)[1].strip()
                message_time = int(timestamp_str)
                current_time = int(time.time())
                
                age = current_time - message_time
                return 0 <= age <= max_age_seconds
        
        return False
    except Exception:
        return False
