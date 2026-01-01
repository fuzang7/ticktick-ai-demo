"""TickTick OAuth2 Authentication Script.

This script handles the OAuth2 authorization flow for TickTick (Dida365) API.
It guides users through obtaining an access token for API access.

Environment Variables Required:
    TICKTICK_CLIENT_ID: OAuth2 client ID from TickTick developer portal
    TICKTICK_CLIENT_SECRET: OAuth2 client secret from TickTick developer portal
    TICKTICK_REDIRECT_URI: Redirect URI registered in TickTick developer portal
"""

import os
import pickle
import time
import logging
import webbrowser
from typing import Optional, Dict, Any
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Configuration with validation
CLIENT_ID = os.getenv("TICKTICK_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("TICKTICK_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv("TICKTICK_REDIRECT_URI", "").strip()

# Default token file
DEFAULT_TOKEN_FILE = ".token-oauth"

# OAuth2 configuration
OAUTH_AUTHORIZE_URL = "https://dida365.com/oauth/authorize"
OAUTH_TOKEN_URL = "https://dida365.com/oauth/token"
SCOPE = "tasks:write tasks:read"


def validate_configuration() -> bool:
    """Validate OAuth2 configuration.

    Returns:
        True if configuration is valid, False otherwise.
    """
    errors = []

    if not CLIENT_ID:
        errors.append("TICKTICK_CLIENT_ID is not set")
    elif len(CLIENT_ID) != 32:  # Typical client ID length
        logger.warning(f"Client ID length is {len(CLIENT_ID)} (expected 32 characters)")

    if not CLIENT_SECRET:
        errors.append("TICKTICK_CLIENT_SECRET is not set")

    if not REDIRECT_URI:
        errors.append("TICKTICK_REDIRECT_URI is not set")
    elif not REDIRECT_URI.startswith(('http://', 'https://')):
        errors.append("Redirect URI must start with http:// or https://")

    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    return True


def generate_auth_url(state: str = "123456") -> str:
    """Generate OAuth2 authorization URL.

    Args:
        state: CSRF protection state parameter.

    Returns:
        Complete OAuth2 authorization URL.
    """
    params = {
        "scope": SCOPE,
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": state
    }

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{OAUTH_AUTHORIZE_URL}?{query_string}"


def extract_auth_code(redirected_url: str) -> Optional[str]:
    """Extract authorization code from redirected URL.

    Args:
        redirected_url: The URL redirected to after authorization.

    Returns:
        Authorization code if found, None otherwise.
    """
    try:
        parsed_url = urlparse(redirected_url)
        query_params = parse_qs(parsed_url.query)

        # Check for code in query parameters
        if 'code' in query_params:
            return query_params['code'][0]
        else:
            # If it's not a full URL, it might be just the code
            if '=' not in redirected_url and len(redirected_url) > 10:
                return redirected_url

    except Exception as e:
        logger.error(f"Failed to parse URL: {e}")

    return None


def exchange_code_for_token(authorization_code: str) -> Optional[Dict[str, Any]]:
    """Exchange authorization code for access token.

    Args:
        authorization_code: The authorization code from OAuth2 flow.

    Returns:
        Token data dictionary if successful, None otherwise.
    """
    payload = {
        "code": authorization_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE
    }

    try:
        logger.info("Exchanging authorization code for access token...")
        response = requests.post(
            OAUTH_TOKEN_URL,
            data=payload,
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
            timeout=30
        )

        logger.info(f"Token endpoint response status: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()

            # Add expiration timestamp
            if 'expires_in' in token_data:
                token_data['expires_at'] = time.time() + token_data['expires_in']

            return token_data
        else:
            logger.error(f"Token request failed with status {response.status_code}")
            try:
                error_data = response.json()
                logger.error(f"Error details: {error_data}")
            except:
                logger.error(f"Response text: {response.text[:200]}")

    except requests.exceptions.Timeout:
        logger.error("Request timeout - please check your internet connection")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
    except ValueError as e:
        logger.error(f"Failed to parse response: {e}")

    return None


def save_token(token_data: Dict[str, Any], token_file: str = DEFAULT_TOKEN_FILE) -> bool:
    """Save token data to file.

    Args:
        token_data: Token data dictionary.
        token_file: Path to token file.

    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        with open(token_file, 'wb') as f:
            pickle.dump(token_data, f)

        logger.info(f"Access token saved to {token_file}")
        logger.info(f"Token expires at: {time.ctime(token_data.get('expires_at', 0))}")
        return True

    except Exception as e:
        logger.error(f"Failed to save token: {e}")
        return False


def main() -> None:
    """Main function to handle OAuth2 authorization flow."""
    print("=" * 60)
    print("TickTick OAuth2 Authentication Script")
    print("=" * 60)
    print()

    # Validate configuration
    if not validate_configuration():
        print("\nPlease create a .env file with the following variables:")
        print("TICKTICK_CLIENT_ID=your_client_id_here")
        print("TICKTICK_CLIENT_SECRET=your_client_secret_here")
        print("TICKTICK_REDIRECT_URI=http://localhost:8080/callback")
        print("\nYou can obtain these credentials from:")
        print("https://developer.dida365.com/openapi")
        return

    print(f"Client ID length: {len(CLIENT_ID)}")
    print(f"Client Secret length: {len(CLIENT_SECRET)}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print()

    # Generate authorization URL
    auth_url = generate_auth_url()
    print("=" * 60)
    print("AUTHORIZATION INSTRUCTIONS:")
    print("=" * 60)
    print("1. Open the following URL in your browser:")
    print(f"\n{auth_url}")
    print("\n2. Log in with your TickTick account if not already logged in")
    print("3. Authorize the application to access your TickTick data")
    print("4. You will be redirected to your redirect URI")
    print("5. Copy the ENTIRE redirected URL from your browser's address bar")
    print("=" * 60)

    # Ask user to open browser
    open_browser = input("\nWould you like to open the URL in your browser? (y/n): ").strip().lower()
    if open_browser in ('y', 'yes'):
        try:
            webbrowser.open(auth_url)
            print("Browser opened. Please follow the instructions above.")
        except Exception as e:
            print(f"Failed to open browser: {e}")
            print("Please manually open the URL shown above.")

    # Get redirected URL from user
    print("\n" + "-" * 40)
    redirected_url = input("Paste the ENTIRE redirected URL here: ").strip()

    # Extract authorization code
    auth_code = extract_auth_code(redirected_url)
    if not auth_code:
        print("ERROR: Could not extract authorization code from the URL.")
        print("Please make sure you copied the COMPLETE redirected URL.")
        return

    print(f"Extracted authorization code (length: {len(auth_code)})")

    # Exchange code for token
    token_data = exchange_code_for_token(auth_code)
    if not token_data:
        print("\nERROR: Failed to obtain access token.")
        print("\nTroubleshooting tips:")
        print("1. Check that your client ID and secret are correct")
        print("2. Make sure you reset your client secret if you changed it")
        print("3. Ensure the redirect URI matches exactly what's in your TickTick developer portal")
        print("4. The authorization code is single-use - you may need to get a new one")
        return

    # Save token
    if save_token(token_data):
        print("\n" + "=" * 60)
        print("✅ SUCCESS: Authentication completed!")
        print("=" * 60)
        print(f"\nAccess token saved to: {DEFAULT_TOKEN_FILE}")
        print(f"Token expires at: {time.ctime(token_data.get('expires_at', 0))}")
        print("\nYou can now use the DidaClient to access the TickTick API.")
    else:
        print("ERROR: Failed to save token file.")


if __name__ == "__main__":
    main()