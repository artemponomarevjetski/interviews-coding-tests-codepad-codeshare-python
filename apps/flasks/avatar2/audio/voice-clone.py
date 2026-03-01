#!/usr/bin/env python3
"""
🎭 Voice Clone Creator for AI Avatar System
Creates your custom voice clone using ElevenLabs API
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_elevenlabs():
    """Install and import ElevenLabs with correct imports"""
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play, save
        return True, (ElevenLabs, play, save)
    except ImportError:
        print("❌ ElevenLabs not installed. Installing now...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "elevenlabs"])
            from elevenlabs.client import ElevenLabs
            from elevenlabs import play, save
            print("✅ ElevenLabs installed successfully!")
            return True, (ElevenLabs, play, save)
        except Exception as e:
            print(f"❌ Failed to install ElevenLabs: {e}")
            return False, None

def get_api_key():
    """Get ElevenLabs API key from user"""
    api_key = os.getenv('ELEVENLABS_API_KEY')
    
    if not api_key or api_key == "your-elevenlabs-api-key-here":
        print("\n🔑 ElevenLabs API Key Required")
        print("=" * 40)
        print("1. Go to https://elevenlabs.io")
        print("2. Sign up/login to your account")
        print("3. Click your profile → API Key")
        print("4. Copy your API key (starts with 'sk_...')")
        print("=" * 40)
        
        api_key = input("Enter your ElevenLabs API key: ").strip()
        
        if not api_key:
            print("❌ No API key provided. Exiting.")
            return None
            
        # Save to .env for future use
        with open('.env', 'a') as f:
            f.write(f"\nELEVENLABS_API_KEY=\"{api_key}\"\n")
        print("✅ API key saved to .env file")
    
    return api_key

def find_audio_samples():
    """Find audio samples for voice cloning"""
    print("\n🎙️  Audio Samples for Voice Cloning")
    print("=" * 50)
    print("Requirements:")
    print("• 1-5 minutes of your voice total")
    print("• Clear recording, no background noise")
    print("• Various phrases and emotions")
    print("• Common formats: MP3, WAV, M4A")
    print("=" * 50)
    
    audio_files = []
    sample_dir = Path("voice_samples")
    
    # Check if voice_samples directory exists
    if sample_dir.exists():
        audio_files = list(sample_dir.glob("*.mp3")) + list(sample_dir.glob("*.wav")) + list(sample_dir.glob("*.m4a"))
        
    if audio_files:
        print(f"✅ Found {len(audio_files)} audio files in 'voice_samples/' folder:")
        for i, file in enumerate(audio_files, 1):
            print(f"   {i}. {file.name}")
        
        use_existing = input("\nUse these files for cloning? (y/n): ").lower().strip()
        if use_existing == 'y':
            return audio_files
    
    print("\n💡 To create audio samples:")
    print("1. Create a 'voice_samples' folder")
    print("2. Record 3-5 audio files of your voice")
    print("3. Include different phrases and emotions")
    print("4. Place files in the 'voice_samples' folder")
    print("5. Run this script again")
    
    input("\nPress Enter to exit and create audio samples...")
    return None

def create_voice_clone(api_key, audio_files):
    """Create voice clone using ElevenLabs"""
    try:
        from elevenlabs.client import ElevenLabs
        
        # Create client
        client = ElevenLabs(api_key=api_key)
        
        print(f"\n🎭 Creating your voice clone...")
        print(f"Using {len(audio_files)} audio samples:")
        for file in audio_files:
            print(f"   📁 {file.name}")
        
        # Create voice clone using the new API
        voice = client.voices.add(
            name=f"Artem Voice Clone - {time.strftime('%Y-%m-%d')}",
            description="AI Avatar voice clone for Artem Ponomarev",
            files=[str(file) for file in audio_files]
        )
        
        print(f"✅ Voice clone created successfully!")
        print(f"🎯 Voice ID: {voice.voice_id}")
        print(f"📛 Voice Name: {voice.name}")
        
        # Save Voice ID to .env
        with open('.env', 'a') as f:
            f.write(f'ELEVENLABS_VOICE_ID="{voice.voice_id}"\n')
        print("✅ Voice ID saved to .env file")
        
        return voice
        
    except Exception as e:
        print(f"❌ Failed to create voice clone: {e}")
        return None

def test_voice_clone(api_key, voice_id):
    """Test the created voice clone"""
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play
        
        client = ElevenLabs(api_key=api_key)
        
        print("\n🧪 Testing your voice clone...")
        
        test_phrases = [
            "Hello! This is my AI avatar voice.",
            "I'm ready to handle conversations on your behalf.",
            "How does my cloned voice sound to you?",
            "This technology is absolutely incredible!"
        ]
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\nTest {i}/4: '{phrase}'")
            audio = client.text_to_speech.convert(
                text=phrase,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2"
            )
            
            # Play the audio
            play(audio)
            time.sleep(1)
        
        print("\n✅ Voice clone test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Voice test failed: {e}")
        return False

def list_existing_voices(api_key):
    """List existing voices in the account"""
    try:
        from elevenlabs.client import ElevenLabs
        
        client = ElevenLabs(api_key=api_key)
        all_voices = client.voices.get_all()
        
        print(f"\n📋 You have {len(all_voices.voices)} voices in your account:")
        
        for i, voice in enumerate(all_voices.voices, 1):
            print(f"{i}. {voice.name} (ID: {voice.voice_id})")
        
        return all_voices.voices
        
    except Exception as e:
        print(f"❌ Failed to list voices: {e}")
        return []

def main():
    """Main voice cloning process"""
    print("🎭 AI Avatar Voice Clone Creator")
    print("=" * 50)
    
    # Setup ElevenLabs
    success, elevenlabs = setup_elevenlabs()
    if not success:
        return
    
    ElevenLabs, play, save = elevenlabs
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        return
    
    # Check for existing voices
    existing_voices = list_existing_voices(api_key)
    
    if existing_voices:
        use_existing = input("\nUse existing voice? (y/n): ").lower().strip()
        if use_existing == 'y':
            print("\nSelect a voice:")
            for i, voice in enumerate(existing_voices, 1):
                print(f"{i}. {voice.name}")
            
            try:
                choice = int(input("Enter number: ")) - 1
                selected_voice = existing_voices[choice]
                
                # Save to .env
                with open('.env', 'a') as f:
                    f.write(f'ELEVENLABS_VOICE_ID="{selected_voice.voice_id}"\n')
                print(f"✅ Using voice: {selected_voice.name}")
                
                # Test the voice
                test_voice_clone(api_key, selected_voice.voice_id)
                return
                
            except (ValueError, IndexError):
                print("❌ Invalid selection")
    
    # Create new voice clone
    print("\n🆕 Creating new voice clone...")
    audio_files = find_audio_samples()
    if not audio_files:
        return
    
    # Create voice clone
    voice = create_voice_clone(api_key, audio_files)
    if not voice:
        return
    
    # Test the new voice clone
    test_voice_clone(api_key, voice.voice_id)
    
    print("\n🎉 Voice cloning setup complete!")
    print("Your AI avatar will now speak with YOUR voice! 🎙️")

if __name__ == "__main__":
    main()
