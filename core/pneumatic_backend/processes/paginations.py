from pneumatic_backend.generics.paginations import DefaultPagination


class WorkflowListPagination(DefaultPagination):

    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        # Count is set in qst
        self.count = queryset.count
        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        # Pagination at the WorkflowListQuery was used
        return queryset
