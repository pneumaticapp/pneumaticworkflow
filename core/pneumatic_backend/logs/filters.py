from django.contrib.admin import SimpleListFilter
from pneumatic_backend.accounts.models import Account


class AccountAdminFilter(SimpleListFilter):

    title = 'Account'
    parameter_name = 'account'

    def lookups(self, request, model_admin):

        choices = []
        qst = (
            Account.objects.filter(log_api_requests=True)
            .order_by('name')
            .values('id', 'name')
        )
        for account in qst:
            choices.append((account['id'], account['name']))
        return choices

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(account_id=self.value())
        return queryset
