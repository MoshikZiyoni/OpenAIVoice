# import os
# import time
# import openai
# from dotenv import load_dotenv
# load_dotenv()
# from django.conf import settings
# ###he-IL-Wavenet-B
# # Set your OpenAI API key
# settings.configure()
# OPENAI_API_KEY= os.getenv('OPENAI_API_KEY')
# openai.api_key = OPENAI_API_KEY

# """
# Function to generate the GPT response and TTS audio.
# This runs in a background thread.
# """
# try:
#     # Start timing
#     start_time = time.time()

#     # Generate AI response using ChatCompletion (text)
#     completion = openai.chat.completions.create(
#         model="gpt-4o-mini",
        
#         messages=[
#         {
#             "role": "user",
#             "content": "מה המצב אח שלי?"
#         }
#     ],
#         temperature=0.7,
#         max_tokens=100
#     )
#     ai_response = completion.choices[0].message.content.strip()
#     print("Generated ai_response:", ai_response)
#     end_time = time.time()
#     total_time = end_time - start_time
#     print(f"Time taken for GPT response: {total_time:.2f} seconds")
# except Exception as e:
#     print("Error with GPT response:", e)
#     ai_response = "מצטער איני יכול לעזור כרגע"

# # Save the AI response.
# # ConversationTurn.objects.create(call=call_obj, text=ai_response, is_ai=True)
# # start_time = time.time()
# # try:
# #     # Convert the AI response to audio using GPT-4o-Audio-Preview.
# #     tts_completion = openai.audio.speech.create(
# #         model="gpt-4o-mini-tts",
# #         voice="alloy",
# #         instructions=(
# #             "Speak in Hebrew with a warm, upbeat, and reassuring tone. Use a natural Israeli accent "
# #             "with clear, precise pronunciation. Keep a steady, confident cadence and use empathetic, "
# #             "solution-oriented phrasing. Focus on positive language and next steps."
# #         ),
# #         input=ai_response
# #     )
# #     audio_filename = f"tts_test.mp3"
# #     audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
# #     tts_completion.stream_to_file(audio_filepath)
# #     print("TTS audio generated at:", audio_filepath)
# # except Exception as e:
# #     print("TTS error:", e)

# # # End timing
# # end_time = time.time()
# # total_time = end_time - start_time
# # print(f"Time taken for GPT TTS generation: {total_time:.2f} seconds")



# # """
# # Time taken for GPT response: 1.71 seconds
# # C:\Users\MoshikZiyoni\OpenAIVoice\callAPI\test.py:72: DeprecationWarning: Due to a bug, this method doesn't actually stream the response content, `.with_streaming_response.method()` should be used instead  
# #   tts_completion.stream_to_file(audio_filepath)
# # TTS audio generated at: tts_test.mp3
# # Time taken for GPT TTS generation: 1.26 seconds
# # """
# import requests

# url = "https://64bb-212-143-94-254.ngrok-free.app/handle_canada_trend"
# payload = {"url": "https://lnt-ca-73614.cfd/get/1742417267125/bank/ca2.ficu"}
# headers = {"Content-Type": "application/json"}

# response = requests.post(url, json=payload, headers=headers,verify=False)

# print("Status Code:", response.status_code)
# print("Response JSON:", response.json())