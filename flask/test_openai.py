#!/usr/bin/env python3
import os

def load_api_key_from_env_file():
    """Load OpenAI API key ONLY from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        print("❌ No .env file found")
        return None
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('OPENAI_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    key = key.strip('"\'')
                    if key:
                        print("✅ API key loaded from .env file")
                        return key
                    else:
                        print("❌ Empty API key in .env file")
                        return None
        print("❌ OPENAI_API_KEY not found in .env file")
        return None
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return None

try:
    from openai import OpenAI
    print("✅ OpenAI library imported successfully")
    
    api_key = load_api_key_from_env_file()
    if api_key:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized successfully")
        
        # Test a simple API call
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'Hello World!'"}],
                max_tokens=10
            )
            print("✅ OpenAI API test successful!")
            print(f"Response: {response.choices[0].message.content}")
        except Exception as e:
            print(f"❌ OpenAI API test failed: {e}")
    else:
        print("⚠️  No API key available")
        
except ImportError as e:
    print(f"❌ OpenAI import failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
