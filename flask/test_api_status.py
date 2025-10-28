#!/usr/bin/env python3
import requests
import os
import json
from datetime import datetime

def test_api_comprehensive():
    print(f"🔍 Testing OpenAI API at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Read API key
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip().strip('"\'')
                    break
            else:
                print("❌ No API key found in .env")
                return
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        return
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-5:]}")
    
    # Test 1: Simple chat completion
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    test_data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Say 'API test successful' only."}],
        "max_tokens": 10
    }
    
    try:
        print("📡 Sending test request to OpenAI...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=test_data,
            timeout=30
        )
        
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print("✅ API TEST SUCCESSFUL!")
            print(f"🤖 Response: {message}")
            
        elif response.status_code == 429:
            print("❌ RATE LIMITED (429)")
            print("💡 This usually means:")
            print("   - Too many requests in short period")
            print("   - Account-level rate limiting")
            print("   - Wait 15-30 minutes")
            
            # Try to get more details
            try:
                error_details = response.json()
                print(f"📋 Error details: {json.dumps(error_details, indent=2)}")
            except:
                print(f"📋 Raw response: {response.text}")
                
        elif response.status_code == 401:
            print("❌ UNAUTHORIZED (401) - Invalid API key")
            print("💡 Check if the API key is correct and active")
            
        elif response.status_code == 403:
            print("❌ FORBIDDEN (403) - Billing issue or restricted")
            print("💡 Check your OpenAI account billing status")
            
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            try:
                error_details = response.json()
                print(f"📋 Error: {json.dumps(error_details, indent=2)}")
            except:
                print(f"📋 Raw: {response.text}")
                
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check internet")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_api_comprehensive()
