from typing import Any

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PagePagination(PageNumberPagination):
    page_size = 3
    max_page_size = 10
    page_size_query_param = 'size'

    def get_page_size(self, request):
        size_param = request.query_params.get(self.page_size_query_param)

        if size_param is None:
            return self.page_size

        try:
            size = int(size_param)
        except (TypeError, ValueError):
            raise ValidationError({
                'size': f"'{size_param}' is not a valid integer."
            })

        if size < 1:
            raise ValidationError({
                'size': 'size must be a positive integer (>= 1).'
            })

        if self.max_page_size and size > self.max_page_size:
            raise ValidationError({
                'size': f'size must not exceed {self.max_page_size}.'
            })

        return size

    def get_paginated_response(self, data:Any) -> Response:
        assert self.page is not None

        return Response({
            'total_items':self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'prev': bool(self.get_previous_link()),
            'next': bool(self.get_next_link()),
            'data': data
        })