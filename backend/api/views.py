from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

# Import modules to import the LLM application.
import sys
from pathlib import Path

# 1. Get the absolute directory of the currently running script
script_dir = Path(__file__).resolve().parent

# 2. Navigate relatively (e.g., up one level to 'my_projects/', then into 'custom_folder/')
target_dir = script_dir / "llm"

# 3. Convert it to a string and insert it into sys.path
sys.path.insert(0, str(target_dir.resolve()))

# 4. Now you can import your module or specific function
from Tutorial_LangGraph_03_MultipleNodesApi import run_graph

# Some imports for handling the user's request by the "View" block in the MVT pattern of Django.
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['POST'])
@authentication_classes([])      # avoid CSRF headaches for a public endpoint
@permission_classes([AllowAny])
def ChatView(request):
    message = request.data.get('message', '').strip()
    if not message:
        return Response({'error': 'message is required'}, status=400)

    try:
        reply = run_graph(message)
        return Response({'reply': reply})
    except Exception as e:
        return Response({'error': str(e)}, status=500)