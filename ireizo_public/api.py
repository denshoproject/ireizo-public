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
            nr_id = record['person']['nr_id']
            ddr_response = models.ddr_objects(nr_id, request)
            ddr_ui_url,ddr_api_url,ddr_status,ddrobjects = ddr_response
            if not status.is_success(ddr_status):
                return Response(
                    {'Internal query HTTP status': ddr_status}, status=ddr_status
                )
            if ddrobjects:
                record['ddr_objects'] = ddrobjects[:5]
                return Response(record)
            return Response(
                {'irei record has no ddr objects': object_id},
                status=status.HTTP_204_NO_CONTENT
            )
    except docstore.NotFoundError:
        return Response(
            {'irei record not found': object_id},
            status=status.HTTP_404_NOT_FOUND
        )
    except KeyError:
        return Response(
            {'irei record has no person': object_id},
            status=status.HTTP_204_NO_CONTENT
        )
