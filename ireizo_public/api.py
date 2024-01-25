from collections import OrderedDict

from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from django.http.request import HttpRequest

from elastictools import docstore, search

from . import models

DEFAULT_LIMIT = 25


# views ----------------------------------------------------------------

@api_view(['GET'])
def index(request, format=None):
    """Swagger UI: /api/swagger/
    """
    data = {}
    return Response(data)


@api_view(['GET'])
def ireirecord(request, object_id, format=None):
    try:
        record = models.IreiRecord.get(object_id, request)
        if record['person'] and record['person']['nr_id']:
            return Response(record)
    except docstore.NotFoundError:
        return Response(
            {'irei_id not found': object_id},
            status=status.HTTP_404_NOT_FOUND
        )
    except KeyError:
        return Response(
            {'irei record has no person': object_id},
            status=status.HTTP_204_NO_CONTENT
        )
