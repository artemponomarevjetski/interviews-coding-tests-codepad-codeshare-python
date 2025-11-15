import base64
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variable from ~/.openai.env
load_dotenv(Path.home() / ".openai.env")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Path to the image
image_path = Path.home() / "temp" / "snap_latest.png"

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analyze_image(path):
    print(f"📷 Analyzing: {path}")
    b64 = image_to_base64(path)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image and comment on anything unusual or notable."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                    ]
                }
            ],
            max_tokens=500
        )
        print("\n💬 GPT says:\n" + response.choices[0].message.content)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if image_path.exists():
        analyze_image(image_path)
    else:
        print(f"❌ Image file not found: {image_path}")
