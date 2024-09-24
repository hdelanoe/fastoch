from decouple import config
from mistralai import Mistral

mistral_api_key = config("MISTRAL_API_KEY", default="", cast=str)
model = "pixtral-12b-2409"

client = Mistral(api_key=mistral_api_key)

chat_response = client.chat.complete(
    model= model,
    messages = [
        {
            "role": "user",
            "content": "Question",
        },
    ]
)
print(chat_response.choices[0].message.content)