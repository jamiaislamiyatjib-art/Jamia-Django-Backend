

from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny

from .models import Center, Lifafa
from .serializers import CenterSerializer, LifafaSerializer
from .pagination import CenterPagination

from rest_framework import viewsets



class CenterViewSet(ModelViewSet):

    queryset = Center.objects.all().prefetch_related("mobile_numbers")
    serializer_class = CenterSerializer
    pagination_class = CenterPagination
    permission_classes = [AllowAny]

    filter_backends = [DjangoFilterBackend, SearchFilter]

    # Filters (exact match)
    filterset_fields = ['state', 'city']

    # Search (partial match)
    search_fields = [
        'center_name',
        'center_id',
        'city',
        'state',
        'pincode',
        'mobile_numbers__mobile'   # ✅ correct way
    ]


# class LifafaViewSet(viewsets.ReadOnlyModelViewSet):

#     serializer_class = LifafaSerializer
#     queryset = Lifafa.objects.all().select_related("center").prefetch_related("papers")

#     def get_queryset(self):
#         queryset = super().get_queryset()

#         center_id = self.request.query_params.get("center_id")

#         if center_id:
#             queryset = queryset.filter(center__center_id=center_id)

#         return queryset

class LifafaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lifafa.objects.all()
    serializer_class = LifafaSerializer
    pagination_class = None   # IMPORTANT FOR PRINT

    def get_queryset(self):
        queryset = super().get_queryset()
        center_id = self.request.query_params.get("center_id")

        if center_id:
            queryset = queryset.filter(center__center_id=center_id)

        return queryset