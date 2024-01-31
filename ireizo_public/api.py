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
    """Returns list of DDR objects for the Person matching an Irei ID
    """
    try:
        ddr_status,api_out = models.irei_person_objects(request, irei_id=object_id)
        if api_out.get('objects') and api_out['objects']:
            return Response(
                api_out,
                status=status.HTTP_200_OK
            )
        if not status.is_success(ddr_status):
            return Response(
                {'ddrpublic API HTTP status': ddr_status},
                status=ddr_status
            )
        return Response(
            {'irei record has no ddr objects': object_id},
            status=status.HTTP_204_NO_CONTENT
        )
    except docstore.NotFoundError:
        return Response(
            {'irei record not found': object_id},
            status=status.HTTP_404_NOT_FOUND
        )
    except models.PersonNotFoundError:
        return Response(
            {'irei record person not found': object_id},
            status=status.HTTP_204_NO_CONTENT
        )
