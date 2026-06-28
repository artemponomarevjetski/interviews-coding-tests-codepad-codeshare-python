import torch
from transformers import pipeline

# Force model to load in float32 so it won't try bfloat16 on MPS.
# Also specify device_map="auto" so it can detect MPS if available,
# but it will use an allowed dtype (float32).
pipe = pipeline(
    "text-generation",
    model="microsoft/phi-4",           # Example model name
    torch_dtype=torch.float32,         # float32 so bfloat16 is avoided
    device_map="auto"                  # will choose MPS if possible, else CPU
)

# Example conversation-like prompt:
messages = [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user",   "content": "Explain quantum computing in simple terms."}
]

# Generate a response:
output = pipe(
    messages,
    max_new_tokens=128,
    # You can also set 'do_sample=True' or 'temperature=0.9' etc. if you want
)

# Print the text from the pipeline result:
print(output[0]["generated_text"])

