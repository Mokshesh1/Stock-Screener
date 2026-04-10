#!/usr/bin/env python3
"""
Zerodha Authentication Helper
Get your enctoken for bot authentication
"""

from kiteconnect import KiteConnect
import json
import webbrowser
from urllib.parse import parse_qs, urlparse

def authenticate_zerodha(api_key: str, api_secret: str) -> str:
    """
    Authenticate with Zerodha and return enctoken
    
    Steps:
    1. Click the login URL
    2. Authorize the app
    3. Paste the request token from redirect URL
    """
    
    print("\n" + "="*70)
    print("ZERODHA AUTHENTICATION HELPER")
    print("="*70 + "\n")
    
    # Initialize Kite
    kite = KiteConnect(api_key=api_key)
    
    # Get login URL
    login_url = kite.login_url()
    print(f"🔗 Login URL (open in browser):\n{login_url}\n")
    
    # Optionally open in browser
    try:
        webbrowser.open(login_url)
        print("✓ Opening browser...")
    except:
        print("⚠ Could not open browser. Copy-paste the URL above.")
    
    # Get request token
    print("\nAfter authorizing in browser, you'll be redirected.")
    print("Copy the 'request_token' parameter from the URL.\n")
    
    request_token = input("Paste request_token here (e.g., abc123...): ").strip()
    
    if not request_token:
        print("✗ No request token provided. Exiting.")
        return None
    
    # Exchange for access token
    try:
        print("\n⏳ Exchanging request token for access token...")
        data = kite.generate_session(request_token, api_secret=api_secret)
        
        access_token = data['access_token']
        print(f"✓ Access token received: {access_token}\n")
        
        return access_token
    
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return None

def get_enctoken_from_browser() -> str:
    """
    Alternative: Get enctoken directly from browser
    Steps:
    1. Log in to kite.zerodha.com
    2. Open DevTools (F12)
    3. Go to Application → Cookies → kite.zerodha.com
    4. Find 'enctoken' cookie and copy value
    """
    
    print("\n" + "="*70)
    print("GET ENCTOKEN FROM BROWSER (Alternative Method)")
    print("="*70 + "\n")
    
    print("Manual Steps:")
    print("1. Open https://kite.zerodha.com/ in your browser")
    print("2. Log in with your Zerodha credentials")
    print("3. Press F12 to open Developer Tools")
    print("4. Go to Application → Cookies → kite.zerodha.com")
    print("5. Find the cookie named 'enctoken'")
    print("6. Copy its value (long alphanumeric string)")
    print("7. Paste below\n")
    
    enctoken = input("Paste enctoken here: ").strip()
    
    if not enctoken or len(enctoken) < 50:
        print("✗ Invalid enctoken. Should be a long alphanumeric string.")
        return None
    
    return enctoken

def update_config(enctoken: str, config_file: str = 'config.json'):
    """Update config.json with enctoken"""
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        config['zerodha']['enctoken'] = enctoken
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Updated {config_file} with enctoken\n")
        return True
    
    except Exception as e:
        print(f"✗ Failed to update config: {e}")
        return False

def verify_authentication(config_file: str = 'config.json') -> bool:
    """Verify if authentication is working"""
    
    from bot import ZerodhaAPI, ConfigManager
    
    print("\n" + "="*70)
    print("VERIFYING AUTHENTICATION")
    print("="*70 + "\n")
    
    try:
        config = ConfigManager(config_file)
        api = ZerodhaAPI(config)
        
        if api.access_token:
            print("✓ Authentication successful!")
            
            # Try to get a quote
            try:
                ltp = api.get_ltp('RELIANCE')
                print(f"✓ Got LTP for RELIANCE: ₹{ltp}")
                return True
            except:
                print("⚠ API connected but couldn't fetch data (market may be closed)")
                return True
        else:
            print("✗ Authentication failed")
            return False
    
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

def main():
    """Main menu"""
    
    print("\n" + "="*70)
    print("ZERODHA BOT AUTHENTICATION")
    print("="*70)
    print("\nChoose authentication method:\n")
    print("1. API Authentication (recommended)")
    print("2. Browser Cookie Method")
    print("3. Verify existing authentication")
    print("4. Exit\n")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        # Load API credentials from config
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            api_key = config['zerodha']['api_key']
            api_secret = config['zerodha']['api_secret']
            
            if not api_key or api_key == 'YOUR_KITE_API_KEY':
                print("\n✗ API key not found in config.json")
                print("Please update config.json with your API credentials first.")
                return
            
            enctoken = authenticate_zerodha(api_key, api_secret)
            
            if enctoken:
                update_config(enctoken)
                print("\n✓ Authentication complete!")
                verify_authentication()
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    elif choice == '2':
        enctoken = get_enctoken_from_browser()
        
        if enctoken:
            update_config(enctoken)
            print("\n✓ Configuration updated!")
            verify_authentication()
    
    elif choice == '3':
        verify_authentication()
    
    elif choice == '4':
        print("\nGoodbye!")
    
    else:
        print("\n✗ Invalid choice")

if __name__ == '__main__':
    main()
