from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardPagination(PageNumberPagination):
    page_size              = 10          # default: 10 per page
    page_size_query_param  = 'page_size' # ?page_size=5  to change
    max_page_size          = 100         # maximum allowed

    def get_paginated_response(self, data):
        return Response({
            'pagination': {
                'total_items'  : self.page.paginator.count,
                'total_pages'  : self.page.paginator.num_pages,
                'current_page' : self.page.number,
                'page_size'    : self.get_page_size(self.request),
                'next'         : self.get_next_link(),
                'previous'     : self.get_previous_link(),
            },
            'results': data
        })