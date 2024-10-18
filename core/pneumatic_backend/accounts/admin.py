from django.db import transaction
from django.contrib.auth import get_user_model, password_validation
from django.conf import settings
from django.contrib import admin
from django import forms
from django.contrib.admin import ModelAdmin, StackedInline
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import resolve_url
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from pneumatic_backend.accounts.models import (
    Account,
    Contact,
    User,
    UserInvite,
    SystemMessage,
    UserGroup,
)
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.payment.enums import BillingPeriod
from pneumatic_backend.accounts.enums import (
    LeaseLevel,
    BillingPlanType,
    UserType,
    SourceType,
    UserStatus,
    Language,
    Timezone,
)
from pneumatic_backend.accounts.services.convert_account import (
    AccountLLConverter
)
from pneumatic_backend.accounts.forms import ContactAdminForm
from pneumatic_backend.authentication.views.mixins import SignUpMixin
from pneumatic_backend.accounts import messages


UserModel = get_user_model()


class UserAdminCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = (
            'email',
            'language',
        )

    email = forms.EmailField(
        label=messages.MSG_A_0015,
        max_length=254,
        required=True
    )
    first_name = forms.CharField(
        label=messages.MSG_A_0016,
        max_length=30,
        required=True
    )
    language = forms.ChoiceField(
        choices=Language.CHOICES,
        initial=settings.LANGUAGE_CODE,
    )
    timezone = forms.ChoiceField(
        choices=Timezone.CHOICES,
        initial=settings.TIME_ZONE,
    )
    password1 = forms.CharField(
        label=messages.MSG_A_0017,
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=messages.MSG_A_0018,
        strip=False,
        help_text=messages.MSG_A_0019,
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        already_exists = UserModel.objects.active().type_user().filter(
            email=email
        ).exists()
        if already_exists:
            raise forms.ValidationError(messages.MSG_A_0005)
        return email


class UserAdminChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = '__all__'

    timezone = forms.ChoiceField(
        choices=Timezone.CHOICES,
        initial=settings.TIME_ZONE,
    )


class GroupAdmin(ModelAdmin):
    model = UserGroup
    list_display = (
        'name',
        'photo',
        'account'
    )
    readonly_fields = [
        'users',
    ]
    ordering = ('name',)
    search_fields = ('name',)


class GroupInline(StackedInline):
    model = UserGroup.users.through
    extra = 0
    verbose_name = 'Group'
    verbose_name_plural = 'Groups'
    show_change_link = True

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(
            GroupInline, self
        ).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'usergroup':
            if request._obj_ is not None:
                field.queryset = field.queryset.filter(
                    account_id=request._obj_.account_id)
            else:
                field.queryset = field.queryset.none()
        return field


class UsersAdmin(UserAdmin, SignUpMixin):

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'language',
                'timezone',
                'password1',
                'password2',
            ),
        }),
    )
    inlines = [GroupInline]
    fieldsets = (
        (
            messages.MSG_A_0020,
            {'fields': (
                'first_name',
                'last_name',
                'email',
                'phone',
                'password',
                'is_account_owner',
                'type',
                'language',
                'timezone',
                'date_fmt',
                'date_fdw',
                'api_key',
                'account_link',
            )}
        ),
        (
            messages.MSG_A_0021,
            {'fields': (
                'is_active',
                'status',
            )}
        ),
        (
            messages.MSG_A_0022,
            {'fields': (
                'is_admin',
                'is_staff',
                'is_superuser',
            )}
        ),
        (
            messages.MSG_A_0023,
            {'fields': (
                'last_login',
                'date_joined',
            )}
        ),
        (
            'Subscription to emails',
            {'fields': (
                'is_digest_subscriber',
                'is_tasks_digest_subscriber',
                'is_special_offers_subscriber',
                'is_newsletters_subscriber',
                'is_new_tasks_subscriber',
                'is_complete_tasks_subscriber',
                'is_comments_mentions_subscriber',
            )}
        )
    )
    list_display = (
        'name',
        'email',
        'is_account_owner',
        'type',
        'status',
        'account_link'
    )
    readonly_fields = (
        'type',
        'account_link',
        'api_key',
    )
    ordering = ('-id',)
    add_form = UserAdminCreationForm
    form = UserAdminChangeForm

    def get_form(self, request, obj=None, **kwargs):
        request._obj_ = obj
        return super(UsersAdmin, self).get_form(request, obj, **kwargs)

    def api_key(self, obj):
        return obj.apikey.key
    api_key.short_description = 'API key'

    def account_link(self, obj):
        url = resolve_url(
            admin_urlname(Account._meta, 'change'),
            obj.account.id
        )
        name = obj.account.name
        return mark_safe(f'<a href={url}>{escape(name)}</a>')

    account_link.short_description = 'Account'
    search_fields = (
        'first_name',
        'last_name',
        'email',
        'phone',
    )
    list_filter = (
        'type',
        'status',
        'is_admin',
        'is_account_owner',
        'is_superuser',
    )

    def delete_model(self, request, obj):

        # TODO remove in https://my.pneumatic.app/workflows/21349/

        account = obj.account
        super().delete_model(request, obj)
        service = AccountService(
            instance=account,
            user=account.get_owner()
        )
        service.update_users_counts()

    def save_model(self, request, obj, form, change):
        if obj.id:
            super().save_model(request, obj, form, change)
            service = AccountService(instance=obj.account, user=obj)
            service.update_users_counts()
        else:
            self.signup(
                email=obj.email,
                first_name=obj.first_name,
                last_name=obj.last_name,
                password=obj._password,
                billing_sync=False,
                request=request
            )


class UserInlineForm(forms.ModelForm):

    class Meta:
        model = UserModel
        fields = (
            'email',
            'first_name',
        )

    email = forms.EmailField(
        label=messages.MSG_A_0015,
        max_length=254,
        required=True
    )
    first_name = forms.CharField(
        label=messages.MSG_A_0016,
        max_length=30,
        required=False
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qst = UserModel.objects.active().type_user().filter(email=email)
        if self.instance:
            qst = qst.exclude(id=self.instance.id)
        already_exists = qst.exists()
        if already_exists:
            self.add_error(field='email', error=messages.MSG_A_0005)
        return email

    def clean_first_name(self):
        value = self.cleaned_data.get('first_name')
        if self.instance.status == UserStatus.ACTIVE and not value:
            self.add_error(field='first_name', error=messages.MSG_A_0024)
        return value

    def save(self, commit=True):
        from pneumatic_backend.accounts.services.user_invite import (
            UserInviteService
        )
        if self.instance.id:
            return super().save(commit=commit)
        else:
            # invite and accept new user
            account = self.cleaned_data['account']
            email = self.cleaned_data['email']
            service = UserInviteService(
                request_user=account.get_owner(),
                current_url='https://api.pneumatic.app/__cp/',
                send_email=False
            )
            service.invite_user(
                email=self.cleaned_data['email'],
                invited_from=SourceType.EMAIL,
            )
            user = account.users.invited().type_user().get(email=email)
            service.accept(
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data.get('last_name'),
                invite=user.invite
            )
            return user


class UserInlineAdmin(StackedInline):

    def role(self, obj) -> str:
        if obj.type == UserType.USER:
            if obj.is_account_owner:
                role = 'Account owner'
            elif obj.is_admin:
                role = 'Admin'
            else:
                role = 'Not admin'
        else:
            role = 'Guest'
        return role

    def password_exists(self, obj):
        return bool(obj.password)
    password_exists.short_description = messages.MSG_A_0017
    password_exists.boolean = True

    model = UserModel
    form = UserInlineForm
    extra = 0
    min_num = 1
    show_change_link = True
    readonly_fields = ('role', 'account', 'password_exists')
    fields = (
        'role',
        'email',
        'first_name',
        'last_name',
        'password_exists',
        'account',
    )


class AccountAdminForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = (
            'name',
            'billing_plan',
            'billing_period',
            'plan_expiration',
            'lease_level',
            'master_account',
            'is_verified',
            'active_users',
            'tenants_active_users',
            'logo_sm',
            'logo_lg',
        )
    name = forms.CharField(required=False)
    logo_sm = forms.CharField(required=False)
    logo_lg = forms.CharField(required=False)
    master_account = forms.IntegerField(required=False)
    billing_plan = forms.ChoiceField(choices=BillingPlanType.CHOICES)
    billing_period = forms.ChoiceField(choices=BillingPeriod.CHOICES)

    def clean_master_account(self):
        value = self.cleaned_data.get('master_account')
        lease_level = self.cleaned_data.get('lease_level')
        if value:
            if lease_level == LeaseLevel.TENANT:
                account = Account.objects.by_id(value).first()
                if account is None:
                    self.add_error(
                        field='master_account',
                        error=messages.MSG_A_0025
                    )
                elif not account.is_subscribed:
                    self.add_error(
                        field='master_account',
                        error=messages.MSG_A_0026
                    )
                else:
                    # TODO remove in https://my.pneumatic.app/workflows/21349/
                    if (
                        self.instance
                        and self.instance.master_account
                        and self.instance.master_account.id != account.id
                    ):
                        self.add_error(
                            field='master_account',
                            error=messages.MSG_A_0027
                        )
                    return account
            else:
                self.add_error(
                    field='master_account',
                    error=messages.MSG_A_0028
                )

        elif not value and lease_level == LeaseLevel.TENANT:
            self.add_error(field='master_account', error=messages.MSG_A_0029)
        return None

    def clean_lease_level(self):

        # TODO remove in https://my.pneumatic.app/workflows/21349/

        new = self.cleaned_data.get('lease_level')
        if self.instance:
            prev = self.instance.lease_level
        else:
            prev = LeaseLevel.STANDARD
        if new != prev:
            allowed_changes = (
                prev == LeaseLevel.STANDARD
                and new in (LeaseLevel.TENANT, LeaseLevel.PARTNER)
            )
            if not allowed_changes:
                self.add_error(
                    field='lease_level',
                    error=messages.MSG_A_0030(prev, new)
                )
        return new

    def clean_logo_sm(self):
        value = self.cleaned_data.get('logo_sm')
        return None if value == '' else value

    def clean_logo_lg(self):
        value = self.cleaned_data.get('logo_lg')
        return None if value == '' else value


class AccountAdmin(ModelAdmin):

    def active_subscription(self, obj):
        return bool(obj.is_subscribed)
    active_subscription.short_description = 'active subscription'
    active_subscription.boolean = True

    def owner_email(self, obj):
        owner = obj.get_owner()
        return owner.email if owner else '-'

    form = AccountAdminForm
    inlines = [UserInlineAdmin]
    fieldsets = [
        (
            messages.MSG_A_0031,
            {
                'fields': (
                    'name',
                    'lease_level',
                    'master_account',
                    'logo_lg',
                    'logo_sm',
                    'is_verified',
                    'log_api_requests',
                )
            }
        ),
        (
            messages.MSG_A_0032,
            {
                'fields': (
                    'billing_sync',
                    'stripe_id',
                    'payment_card_provided',
                    'trial_ended',
                    'trial_is_active',
                    'trial_start',
                    'trial_end',
                    'billing_plan',
                    'billing_period',
                    'plan_expiration',
                    'max_users',
                    'active_users',
                    'tenants_active_users',
                    'max_active_templates',
                    'active_templates',
                    'max_invites',
                    'ai_templates_generations',
                    'max_ai_templates_generations',
                )
            }
        ),
        (
            messages.MSG_A_0033,
            {
                'fields': (
                    'list_tenants',
                )
            }
        )
    ]
    readonly_fields = [
        'stripe_id',
        'active_users',
        'tenants_active_users',
        'max_users',
        'active_templates',
        'list_tenants',
        'ai_templates_generations',
        'trial_is_active',
    ]
    list_display = (
        'name',
        'owner_email',
        'billing_sync',
        'active_subscription',
        'billing_plan',
        'billing_period',
        'plan_expiration',
        'active_users',
        'max_users',
        'lease_level',
        'master_account',
    )

    list_filter = (
        'lease_level',
        'billing_plan',
        'billing_period',
        'billing_sync',
        'log_api_requests',
    )
    search_fields = ('name', 'users__email', 'stripe_id')
    ordering = ('-id',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prev_lease_level = None

    def list_tenants(self, obj):
        result = list()
        for acc in obj.tenants.only_tenants():
            url = resolve_url(admin_urlname(acc._meta, 'change'), acc.id)
            result.append(
                f'<li><a target="_blank" '
                f'href={url}>{escape(acc.name)} [{acc.id}]</a></li>'
            )
        result = ''.join(result)
        if result:
            return mark_safe(f'<ul>{result}</ul>')
        else:
            return '-'
    list_tenants.short_description = 'Tenants'

    def get_object(self, request, object_id, from_field=None):
        result = super().get_object(request, object_id, from_field)
        if result:
            self.prev_lease_level = result.lease_level
        return result

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """

        service = AccountService(
            instance=obj,
            user=request.user
        )
        with transaction.atomic():
            if obj.billing_plan == BillingPlanType.PREMIUM:
                max_users = obj.get_paid_users_count()
            elif obj.billing_plan == BillingPlanType.FREEMIUM:
                max_users = settings.FREEMIUM_MAX_USERS
            else:
                max_users = 1000
            obj = service.partial_update(
                name=obj.name,
                billing_sync=obj.billing_sync,
                billing_plan=obj.billing_plan,
                billing_period=obj.billing_period,
                trial_start=obj.trial_start,
                trial_end=obj.trial_end,
                trial_ended=obj.trial_ended,
                plan_expiration=obj.plan_expiration,
                lease_level=obj.lease_level,
                master_account=obj.master_account,
                is_verified=obj.is_verified,
                logo_sm=obj.logo_sm,
                logo_lg=obj.logo_lg,
                max_users=max_users,
                max_active_templates=obj.max_active_templates,
                max_invites=obj.max_invites,
                max_ai_templates_generations=obj.max_ai_templates_generations,
                payment_card_provided=obj.payment_card_provided,
                log_api_requests=obj.log_api_requests,
                force_save=True
            )
            converter = AccountLLConverter(
                instance=obj,
                user=request.user
            )
            converter.handle(
                prev=self.prev_lease_level,
                new=obj.lease_level
            )

    def delete_model(self, request, obj):

        # TODO remove in https://my.pneumatic.app/workflows/21349/

        if obj.tenants.only_tenants().exists():
            raise Exception(messages.MSG_A_0034)
        master_account = obj.master_account if obj.is_tenant else None
        super().delete_model(request, obj)

        if master_account:
            service = AccountService(
                instance=master_account,
                user=master_account.get_owner()
            )
            service.update_users_counts()

    def has_add_permission(self, request):
        return False


class SystemMessageAdmin(ModelAdmin):
    list_display = ('id', 'title', 'publication_date')

    readonly_fields = ('is_delivery_completed', )


class ContactAdmin(ModelAdmin):

    def photo_preview(self, obj):
        if obj.photo:
            return mark_safe(
                f'<image src={obj.photo} style="max-width: 200px;">'
            )
        return '-'

    def photo_exists(self, obj):
        return bool(obj.photo)

    photo_exists.short_description = 'Photo'
    photo_exists.boolean = True

    form = ContactAdminForm
    fields = (
        'photo',
        'photo_file',
        'photo_preview',
        'first_name',
        'last_name',
        'job_title',
        'source',
        'email',
        'user',
        'account',
        'status',
    )
    readonly_fields = (
        'account',
        'photo_preview',
    )

    raw_id_fields = (
        'user',
    )
    list_filter = (
        'source',
        'status',
    )
    list_display = (
        'name',
        'email',
        'job_title',
        'source',
        'user',
        'photo_exists'
    )
    search_fields = (
        'email',
        'first_name',
        'last_name',
        'job_title',
    )


admin.site.register(User, UsersAdmin)
admin.site.register(UserGroup, GroupAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(UserInvite)
admin.site.register(SystemMessage, SystemMessageAdmin)
admin.site.register(Contact, ContactAdmin)

admin.site.site_header = 'Pneumatic admin'
admin.site.index_title = 'Apps'
