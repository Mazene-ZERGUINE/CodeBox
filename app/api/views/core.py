from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class CoreViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['GET'], url_path='ping')
    def ping(self, request, pk=None):
        return Response({'Status': 'Server is Alive'})
