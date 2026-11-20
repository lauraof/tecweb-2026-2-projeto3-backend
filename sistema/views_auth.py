from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from sistema.serializers import CadastroSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def cadastro_endpoint(request):
    serializer = CadastroSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)