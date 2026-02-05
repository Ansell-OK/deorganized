# This file contains old endpoint implementations and has been replaced
# by the new wallet authentication implementation in views.py
#
# DO NOT USE THIS FILE
# 
# The correct implementation is now in views.py:
# - get_auth_message() - generates nonce
# - login_or_register() - creates users immediately + issues tokens
# - complete_setup() - updates profile post-auth
#
# See WALLET_AUTH_API.md for complete documentation
#
# This file is kept for reference only and will be deleted in future cleanup.
