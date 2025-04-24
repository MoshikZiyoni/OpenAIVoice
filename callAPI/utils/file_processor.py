# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# import pandas as pd
# import os

# @csrf_exempt
# @require_http_methods(["POST"])
# def bulk_calls(request):
#     """Handle bulk calls from a CSV file."""
#     if request.method == 'POST':
#         csv_file = request.FILES.get('file')
#         if not csv_file:
#             return JsonResponse({"error": "No file provided"}, status=400)

#         try:
#             # Read the CSV file using pandas with UTF-8 encoding
#             df = pd.read_csv(csv_file, encoding='utf-8')

#             # Ensure the DataFrame has the required columns
#             if not {'name', 'phone_number'}.issubset(df.columns):
#                 return JsonResponse({"error": "CSV must contain 'name' and 'phone_number' columns"}, status=400)

#             # Process calls in chunks of 10
#             for i in range(0, len(df), 10):
#                 chunk = df.iloc[i:i + 10]
#                 # Here you would initiate calls using the Twilio API
#                 # Example: initiate_calls(chunk['phone_number'].tolist())

#             return JsonResponse({"success": True, "message": "Calls initiated"})

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)