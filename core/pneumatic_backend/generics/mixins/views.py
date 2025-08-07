import hashlib
from typing import List, Optional, Tuple
from django.conf import settings
from django.core.cache import caches
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from pneumatic_backend.processes.models import Template
from pneumatic_backend.processes.utils.common import get_prefetch_fields


class BaseResponseMixin:

    default_bad_request_data = None

    def response_bad_request(self, data: Optional[dict] = None):
        return Response(
            data=data or self.default_bad_request_data,
            status=status.HTTP_400_BAD_REQUEST
        )

    def response_ok(self, data=None):
        if data is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(data=data, status=status.HTTP_200_OK)

    def response_raw(self, data=None):
        return HttpResponse(content=data)

    def response_created(self, data):
        return Response(data=data, status=status.HTTP_201_CREATED)

    def response_not_found(self):
        return Response(status=status.HTTP_404_NOT_FOUND)

    def redirect(self, redirect_to):
        return HttpResponseRedirect(redirect_to=redirect_to)


class ActionViewMixin:
    action_serializer_classes = {}
    action_filterset_classes = {}
    action_permission_classes = {}

    def get_serializer_class(self):
        if self.action not in self.action_serializer_classes:
            return super().get_serializer_class()

        return self.action_serializer_classes[self.action]

    def get_permissions(self):
        if self.action not in self.action_permission_classes:
            return super().get_permissions()

        return self.action_permission_classes[self.action]


class BasePrefetchMixin:
    def prefetch_queryset(self, queryset, extra_fields: List[str] = None):
        prefetch_fields = []

        try:
            serializer_class = self.get_serializer_class()
        except AssertionError:
            serializer_class = None

        if serializer_class is not None:
            prefetch_fields = get_prefetch_fields(serializer_class)

        if extra_fields is not None:
            prefetch_fields.extend(extra_fields)

        return queryset.prefetch_related(*prefetch_fields)


class BaseContextMixin:

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context(
            **kwargs.pop('extra_fields', {})
        )
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self, **kwargs):
        context = super(BaseContextMixin, self).get_serializer_context()
        context.update(kwargs)
        return context


class BasePaginationMixin:

    action_paginator_classes = {}

    @property
    def paginator(self):

        """

        @property
        def paginator(self):

            if not hasattr(self, '_paginator'):
                if self.pagination_class is None:
                    self._paginator = None
                else:
                    self._paginator = self.pagination_class()
            return self._paginator

        """
        if not hasattr(self, '_paginator'):
            if self.action not in self.action_paginator_classes:
                return super().paginator
            self._paginator = self.action_paginator_classes[self.action]()
        return self._paginator

    def paginated_response(self, queryset):
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.response_ok(serializer.data)


class CustomViewSetMixin(
    ActionViewMixin,
    BaseContextMixin,
    BasePrefetchMixin,
    BasePaginationMixin,
    BaseResponseMixin,
):
    pass


class AnonymousMixin:

    """ Class represent actions with anonymous users """

    cache = caches[getattr(settings, 'ANON_USER_CACHE', 'default')]
    cache_prefix = getattr(settings, 'ANON_USER_CACHE_PREFIX', 'au:')
    cache_timeout = getattr(settings, 'ANON_USER_CACHE_TIMEOUT', 2592000)

    def get_cache_key(self, key_parts: Tuple) -> str:
        return self.cache_prefix + hashlib.md5(
            ''.join(key_parts).encode('utf-8')
        ).hexdigest()

    def get_user_ip(self, request: Request) -> Optional[str]:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if isinstance(x_forwarded_for, str):
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.headers.get(
                'Remote-Addr',
                request.META.get('REMOTE_ADDR')
            )
        return ip

    def get_user_agent(self, request: Request) -> str:
        return request.headers.get(
            'User-Agent',
            request.META.get('HTTP_USER_AGENT')
        )


class AnonymousWorkflowMixin(AnonymousMixin):

    def anonymous_user_workflow_exists(
        self,
        request: Request,
        template: Template
    ) -> Optional[bool]:

        """ Returns True if the anonymous user has already
            created a workflow using specific template
            Returns None if user ip not found in request headers """

        user_ip = self.get_user_ip(request)
        if user_ip is None:
            return None
        cache_key = self.get_cache_key(key_parts=(str(template.id), user_ip))
        count_created_workflows = self.cache.get(cache_key, 0)
        return count_created_workflows > 0

    def inc_anonymous_user_workflow_counter(
        self,
        request,
        template: Template
    ):

        """ Increases the counter of the number of workflow created by
            the anonymous user """

        user_ip = self.get_user_ip(request)
        cache_key = self.get_cache_key(key_parts=(str(template.id), user_ip))
        added = self.cache.add(cache_key, 1, timeout=self.cache_timeout)
        if not added:
            self.cache.incr(cache_key)


class AnonymousAccountMixin(AnonymousMixin):

    def anonymous_user_account_exists(
        self,
        request
    ) -> Optional[bool]:

        """ Returns True if the anonymous user has already
            created a account
            Returns None if user ip not found in request headers """

        user_ip = self.get_user_ip(request)
        if user_ip is None:
            return None
        cache_key = self.get_cache_key(key_parts=('accounts', user_ip))
        count_created_accounts = self.cache.get(cache_key, 0)
        return count_created_accounts > 0

    def inc_anonymous_user_account_counter(
        self,
        request,
    ):

        """ Increases the counter of the number of accounts created by
            the anonymous user """

        user_ip = self.get_user_ip(request)
        cache_key = self.get_cache_key(key_parts=('accounts', user_ip))
        added = self.cache.add(cache_key, 1, timeout=self.cache_timeout)
        if not added:
            self.cache.incr(cache_key)
