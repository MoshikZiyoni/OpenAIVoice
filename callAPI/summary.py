# from django.http import HttpResponse, JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# from django.conf import settings
# from .models import Call
# import logging
# logger = logging.getLogger(__name__)


# @csrf_exempt
# @require_http_methods(["GET", "POST"])
# def handle_summary(request):
#     logger.info("Request", request)
#     return