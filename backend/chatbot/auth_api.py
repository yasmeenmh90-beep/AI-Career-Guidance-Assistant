import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.middleware.csrf import get_token

@require_GET
def auth_status(request):
    # Ensure CSRF cookie is set
    get_token(request)
    if request.user.is_authenticated:
        return JsonResponse({
            "authenticated": True,
            "user": request.user.username,
            "email": request.user.email
        })
    return JsonResponse({"authenticated": False})

@csrf_exempt
@require_POST
def api_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({"error": "Username and password are required"}, status=400)
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({"success": True, "user": user.username})
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=401)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_POST
def api_logout(request):
    logout(request)
    return JsonResponse({"success": True})

@csrf_exempt
@require_POST
def api_signup(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({"error": "Username and password are required"}, status=400)
            
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)
            
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return JsonResponse({"success": True, "user": user.username})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
