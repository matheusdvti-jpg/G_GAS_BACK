from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data.get('detail', response.data) if isinstance(response.data, dict) else response.data
    response.data = {
        'status': 'error',
        'detail': detail,
    }
    return response
