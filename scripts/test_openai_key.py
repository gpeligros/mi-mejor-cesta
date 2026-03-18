from openai import OpenAI

API_KEY = "sk-proj-LOQUESEA..."  # misma clave que en tu script grande
client = OpenAI(api_key=API_KEY)

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "Eres un asistente."},
        {"role": "user", "content": "Responde solo 'OK'."},
    ],
    temperature=0,
)

print("Respuesta del modelo:", resp.choices[0].message.content)
