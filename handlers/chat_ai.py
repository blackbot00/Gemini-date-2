import openai
from config import OPENROUTER_API_KEY

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

async def get_ai_response(user_msg, personality, gender):
    # Personality check for 18+ (Premium only logic goes here)
    system_prompt = f"You are a {personality} partner. Speak to a {gender} user. Keep it realistic."
    
    response = client.chat.completions.create(
        model="google/gemini-2.0-flash-exp:free", # Or any model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
    )
    return response.choices[0].message.content
  
