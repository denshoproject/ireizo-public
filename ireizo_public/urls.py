from django.urls import include, path, re_path
from drf_yasg import views as yasg_views
from drf_yasg import openapi
from rest_framework import permissions

from . import api


schema_view = yasg_views.get_schema_view(
   openapi.Info(
      title="Densho Ireizo API",
      default_version='1.0',
      description='DESCRIPTION TEXT GOES HERE',
      terms_of_service="http://ddr.densho.org/terms/",
      contact=openapi.Contact(email="info@densho.org"),
      #license=openapi.License(name="TBD"),
   ),
   #validators=['flex', 'ssv'],
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('api/swagger.json',
         schema_view.without_ui(cache_timeout=0), name='schema-json'
    ),
    path('api/swagger.yaml',
         schema_view.without_ui(cache_timeout=0), name='schema-yaml'
    ),
    path('api/swagger/',
         schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'
    ),
    path('api/redoc/',
         schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'
    ),
    re_path(
        r'^api/1.0/(?P<object_id>[0-9a-zA-Z_:-]+)',
        api.ireirecord, name='ireizo-api-ireirecord'
    ),
    path('api/1.0/', api.index, name='ireizo-api-index'),
    path('', api.index, name='ireizo-index'),
]
