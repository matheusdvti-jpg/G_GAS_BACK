from django.db import transaction
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.common.texts.messages import RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO
from AppCore.core.exceptions.exceptions import NotFoundException, SystemErrorException


def _build_success_response(resultado, success_message):
    if not resultado:
        resultado = {}
    message = resultado.get('message') or success_message or 'Sucesso'
    success_resultado = {
        'status': 'success',
        'message': message,
    }
    if 'data' in resultado:
        success_resultado['data'] = resultado['data']
    return success_resultado, resultado.get('status_code', status.HTTP_200_OK)


class BasicPostAPIView(GenericAPIView):
    http_method_names = ['post']
    success_message = ''

    def do_action_post(self, serializer, request, *args, **kwargs):
        raise SystemErrorException('Este método não foi implementado.')

    @handle_exceptions
    def post(self, request, *args, **kwargs):
        serializer_object = self.get_serializer(data=request.data)
        serializer_object.is_valid(raise_exception=True)
        resultado = {}
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                resultado = self.do_action_post(serializer_object, request, *args, **kwargs) or {}
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        data, status_code = _build_success_response(resultado, self.success_message)
        return Response(data, status=status_code)


class BasicListAPIView(GenericAPIView):
    http_method_names = ['get']
    success_message = ''
    filter_backends = [DjangoFilterBackend]

    def validate_get(self, request, *args, **kwargs):
        pass

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        self.validate_get(request, *args, **kwargs)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            data = {
                'status': 'success',
                'message': self.success_message or 'Sucesso',
                'count': paginated_response.data.get('count'),
                'next': paginated_response.data.get('next'),
                'previous': paginated_response.data.get('previous'),
                'data': paginated_response.data.get('results'),
            }
            return Response(data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                'status': 'success',
                'message': self.success_message or 'Sucesso',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class BasicDeleteAPIView(GenericAPIView):
    http_method_names = ['delete']

    def do_action_delete(self, request, *args, **kwargs):
        self.object.delete()

    @handle_exceptions
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            raise NotFoundException(RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO)
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                self.do_action_delete(request, *args, **kwargs)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BasicUpdateAPIView(GenericAPIView):
    http_method_names = ['patch']
    success_message = ''

    def do_action_patch(self, serializer, request, *args, **kwargs):
        for field, value in serializer.validated_data.items():
            setattr(self.object, field, value)
        self.object.save()

    @handle_exceptions
    def patch(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            raise NotFoundException(RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO)
        serializer_object = self.get_serializer(data=request.data, partial=True)
        serializer_object.is_valid(raise_exception=True)
        resultado = {}
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                resultado = self.do_action_patch(serializer_object, request, *args, **kwargs) or {}
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        data, status_code = _build_success_response(resultado, self.success_message)
        return Response(data, status=status_code)


class BasicGetAPIView(GenericAPIView):
    http_method_names = ['get']
    success_message = ''

    def validate_retrieve(self, request, *args, **kwargs):
        pass

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        self.validate_retrieve(request, *args, **kwargs)
        try:
            self.object = self.get_object()
        except Http404:
            raise NotFoundException(RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO)
        serializer = self.get_serializer(self.object)
        return Response(
            {
                'status': 'success',
                'message': self.success_message or 'Sucesso',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK,
        )
