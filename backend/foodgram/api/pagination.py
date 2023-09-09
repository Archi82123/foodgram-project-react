from rest_framework.pagination import PageNumberPagination


class SignUpPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 50
    page_size_query_param = 'limit'
