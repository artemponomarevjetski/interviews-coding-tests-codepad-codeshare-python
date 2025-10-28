#!/usr/bin/env python3
import requests
import os
from datetime import datetime

def check_usage():
    print("💰 OpenAI Usage Check")
    print("=" * 50)
    
    # Read API key
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip().strip('"\'')
                    break
    except:
        print("❌ Could not read API key from .env")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # Get current date for usage checking
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📅 Checking usage for: {today}")
    print("🔗 Opening billing pages...")
    
    import webbrowser
    webbrowser.open("https://platform.openai.com/account/usage")
    webbrowser.open("https://platform.openai.com/account/billing")
    
    print("\n💡 Manual Check Instructions:")
    print("1. Visit: https://platform.openai.com/account/usage")
    print("2. Check 'Usage' tab for daily costs")
    print("3. Visit: https://platform.openai.com/account/billing")
    print("4. See your $10.00 balance and auto-recharge settings")
    print("\n📊 GPT-3.5 Turbo Pricing:")
    print("   - Input:  $0.0015 per 1K tokens")
    print("   - Output: $0.0020 per 1K tokens")
    print("   - ~500-1000 tokens per screenshot analysis")

if __name__ == "__main__":
    check_usage()
