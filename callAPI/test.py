# import os
# import openai
# from dotenv import load_dotenv
# load_dotenv()
# from django.conf import settings

# # Set your OpenAI API key
# settings.configure()
# OPENAI_API_KEY= os.getenv('OPENAI_API_KEY')
# openai.api_key = OPENAI_API_KEY

# try:
#     completion = openai.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages="hello",
#         temperature=0.7,
#     )
#     ai_response = completion.choices[0].message.content.strip()
#     print("ai_response: " , ai_response)
# except Exception as e:
#     print("Error with gpt-3.5", e)

import os
import requests
# Define the full path to the file
hey_audio_url='https://web-production-7204.up.railway.app/media/Hey.mp3'
response = requests.get(hey_audio_url)
print(response.status_code)