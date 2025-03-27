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
from .models import MediaFile

# Define the full path to the file
file_path = r'C:\Users\MoshikZiyoni\OpenAIVoice\OpenAIVoice\media\Hey.mp3'

# Check if the file exists
if os.path.exists(file_path):
    # Open the file in binary mode
    with open(file_path, 'rb') as file:
        # Create a MediaFile instance and save it to the database
        media_file = MediaFile.objects.create(name='Hey.mp3', file='media/Hey.mp3')
        media_file.save()
        print("File saved to the database:", media_file)
else:
    print("File does not exist at:", file_path)