"""
Wallet Authentication ViewSet

Provides endpoints for nonce-based wallet authentication using Stacks wallets.

Endpoints:
    POST /api/auth/wallet/nonce/ - Generate authentication nonce
    POST /api/auth/wallet/verify/ - Verify signature and authenticate
"""

import uuid
import time
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    WalletNonceRequestSerializer,
    WalletSignatureVerifySerializer,
    WalletUserSerializer
)
from .crypto_utils import verify_stacks_signature

User = get_user_model()

# Configuration
NONCE_EXPIRATION = 300  # 5 minutes
APP_NAME = "Deorganized"


class WalletAuthViewSet(viewsets.ViewSet):
    """
    ViewSet for wallet-based authentication.
    
    Provides a two-step authentication flow:
    1. Request nonce - generates a unique challenge
    2. Verify signature - validates wallet ownership and authenticates
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='nonce')
    def nonce(self, request):
        """
        Generate an authentication nonce.
        
        POST /api/auth/wallet/nonce/
        
        Request body:
            {
                "wallet_address": "SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7"
            }
        
        Response:
            {
                "message": "Sign this message to authenticate with Deorganized.\\n\\nWallet: SP2J6ZY...\\nNonce: abc123\\nTimestamp: 1642435200"
            }
        
        Security:
            - Nonce expires after 5 minutes
            - Each wallet can have only one active nonce at a time
            - Nonce is single-use (deleted after verification)
        """
        serializer = WalletNonceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        
        # Generate secure nonce
        nonce = uuid.uuid4().hex
        timestamp = int(time.time())
        
        # Create message for signing
        # Format is human-readable and includes anti-phishing elements
        message = (
            f"Sign this message to authenticate with {APP_NAME}.\n\n"
            f"Wallet: {wallet_address}\n"
            f"Nonce: {nonce}\n"
            f"Timestamp: {timestamp}\n\n"
            f"This request will expire in 5 minutes."
        )
        
        # Store nonce in cache with expiration
        cache_key = f'wallet_nonce_{wallet_address}'
        cache.set(cache_key, {
            'nonce': nonce,
            'timestamp': timestamp,
            'message': message
        }, timeout=NONCE_EXPIRATION)
        
        return Response({
            'message': message,
            'expires_in': NONCE_EXPIRATION
        })
    
    @action(detail=False, methods=['post'], url_path='verify')
    def verify(self, request):
        """
        Verify wallet signature and authenticate user.
        
        POST /api/auth/wallet/verify/
        
        Request body:
            {
                "wallet_address": "SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7",
                "signature": "0x3045022100...",
                "message": "Sign this message..."
            }
        
        Response (success):
            {
                "user": {
                    "id": 1,
                    "username": "user_SP2J6ZY4",
                    "stacks_address": "SP2J6ZY...",
                    "is_new": false
                },
                "tokens": {
                    "access": "eyJ0eXAi...",
                    "refresh": "eyJ0eXAi..."
                }
            }
        
        Security checks:
            1. Nonce must exist and not be expired
            2. Nonce must match the one in the message
            3. Message must match the exact message we generated
            4. Signature must cryptographically verify
            5. Nonce is deleted after successful verification (single-use)
        """
        serializer = WalletSignatureVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        signature = serializer.validated_data['signature']
        message = serializer.validated_data['message']
        
        # Retrieve nonce from cache
        cache_key = f'wallet_nonce_{wallet_address}'
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            return Response({
                'error': 'Invalid or expired nonce. Please request a new authentication message.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify message matches exactly
        if cached_data['message'] != message:
            cache.delete(cache_key)
            return Response({
                'error': 'Message does not match the issued nonce. Please request a new nonce.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify nonce is in the message
        if cached_data['nonce'] not in message:
            cache.delete(cache_key)
            return Response({
                'error': 'Invalid nonce in message'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cryptographically verify the signature
        is_valid_signature = verify_stacks_signature(
            wallet_address,
            message,
            signature
        )
        
        if not is_valid_signature:
            cache.delete(cache_key)
            return Response({
                'error': 'Invalid signature. Signature verification failed.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Delete nonce to prevent replay attacks
        cache.delete(cache_key)
        
        # Get or create user
        user, created = User.objects.get_or_create(
            stacks_address=wallet_address,
            defaults={
                'username': self._generate_username(wallet_address),
                'email': '',  # Email is optional for wallet users
                'role': 'user'
            }
        )
        
        # Add is_new flag to user object (for serializer)
        user.is_new = created
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Serialize user data
        user_serializer = WalletUserSerializer(user)
        
        return Response({
            'user': user_serializer.data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_200_OK)
    
    def _generate_username(self, wallet_address: str) -> str:
        """
        Generate a unique username from wallet address.
        
        Args:
            wallet_address: The Stacks wallet address
        
        Returns:
            str: A unique username
        """
        # Base username from first 8 chars of address
        base_username = f'user_{wallet_address[:8]}'
        username = base_username
        
        # Ensure uniqueness
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}_{counter}'
            counter += 1
        
        return username
