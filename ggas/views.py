from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import AllowAnyMixin


class HealthView(AllowAnyMixin, APIView):
    @extend_schema(tags=['Sistema'], summary='Verifica se a API e o SQLite respondem')
    @handle_exceptions
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return Response(
            {
                'status': 'success',
                'message': 'API no ar.',
                'data': {'banco': 'sqlite'},
            }
        )
