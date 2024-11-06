import uuid
from datetime import timedelta
from typing import Set, Dict
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import UniqueConstraint, Q, Manager
from django.utils import timezone
from pneumatic_backend.accounts.enums import (
    NotificationType,
    NotificationStatus,
    UserStatus,
    UserType,
    BillingPlanType,
    SourceType,
    UserInviteStatus,
    LeaseLevel,
    Language,
    UserDateFormat,
    UserFirstDayWeek,
    Timezone,
)
from pneumatic_backend.accounts.fields import (
    EmailLowerField,
    TruncatingCharField
)
from pneumatic_backend.accounts.querysets import (
    UserInviteQuerySet,
    UserQuerySet,
    AccountQuerySet,
    AccountSystemTemplateQuerySet,
    APIKeyQuerySet,
    NotificationsQuerySet,
    InactiveUserQuerySet,
    SystemMessageQuerySet,
    GuestQuerySet,
    ContactQuerySet,
    GroupQuerySet,
)
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.accounts.managers import (
    SoftDeleteUserManager,
    SoftDeleteGuestManager
)
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.payment.enums import BillingPeriod


class Account(SoftDeleteModel):

    class Meta:
        ordering = ['id']

    name = models.TextField(
        verbose_name='Company name',
        default='Company name',
    )
    date_joined = models.DateTimeField(default=timezone.now)
    billing_sync = models.BooleanField(
        default=True,
        verbose_name='Stripe synchronization'
    )
    billing_plan = models.CharField(
        max_length=255,
        default=BillingPlanType.FREEMIUM
    )
    billing_period = models.CharField(
        max_length=255,
        choices=BillingPeriod.CHOICES,
        default=None,
        null=True
    )
    plan_expiration = models.DateTimeField(blank=True, null=True)
    trial_ended = models.BooleanField(
        default=False,
        help_text='Indicates that the trial is no longer available'
    )
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    payment_card_provided = models.BooleanField(default=False)
    stripe_id = models.CharField(max_length=255, null=True)
    system_templates = models.ManyToManyField(
        'processes.SystemTemplate',
        related_name='account_system_template',
        through='AccountSystemTemplate',
    )
    max_users = models.IntegerField(default=settings.FREEMIUM_MAX_USERS)
    max_invites = models.IntegerField(default=settings.MAX_INVITES)
    max_active_templates = models.IntegerField(
        default=settings.PAYWALL_MAX_ACTIVE_TEMPLATES
    )
    ai_templates_generations = models.PositiveIntegerField(default=0)
    max_ai_templates_generations = models.IntegerField(default=1000)
    active_users = models.IntegerField(default=1)
    tenants_active_users = models.IntegerField(default=0)
    active_templates = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=True)
    lease_level = models.CharField(
        choices=LeaseLevel.CHOICES,
        default=LeaseLevel.STANDARD,
        max_length=50
    )
    logo_sm = models.URLField(
        max_length=1024,
        null=True,
        help_text='80px x 80px'
    )
    logo_lg = models.URLField(
        max_length=1024,
        null=True,
        help_text='340px x 96px'
    )
    master_account = models.ForeignKey(
        'Account',
        on_delete=models.SET_NULL,
        related_name='tenants',
        null=True
    )
    tenant_name = models.CharField(
        verbose_name='Tenant name',
        null=True,
        blank=True,
        max_length=255
    )
    tmp_subscription = models.BooleanField(
        default=False,
        help_text=(
            'The system flag means that the temporary subscription changes '
            'is enabled and stripe webhook about changes not received yet'
        )
    )
    log_api_requests = models.BooleanField(default=False)

    objects = BaseSoftDeleteManager.from_queryset(AccountQuerySet)()

    def is_verification_timed_out(self):
        if settings.VERIFICATION_CHECK:
            time_after_register = timezone.now() - self.date_joined
            return not self.is_verified and time_after_register > timedelta(
                days=settings.VERIFICATION_DEADLINE_IN_DAYS
            )
        return False

    def get_owner(self):
        return self.users.filter(is_account_owner=True).first()

    @property
    def is_paid(self):

        """ Return True if the user is paying for a subscription now """

        if self.billing_plan == BillingPlanType.FREEMIUM:
            # Free plan
            return False
        elif self.trial_is_active:
            # Active trial
            return False
        elif self.plan_expiration < timezone.now():
            # Expired premium
            return False
        # Active premium
        return True

    @property
    def is_subscribed(self):

        """ Return True if the user has active subscription or trial """

        return (
            self.billing_plan != BillingPlanType.FREEMIUM
            and self.plan_expiration
            and self.plan_expiration > timezone.now()
        )

    @property
    def is_expired(self):

        """ Return True if the user has expired subscription """

        return (
            self.billing_plan != BillingPlanType.FREEMIUM
            and self.plan_expiration
            and self.plan_expiration < timezone.now()
        )

    @property
    def trial_is_active(self):
        current_date = timezone.now()
        r = bool(
            not self.trial_ended
            and self.billing_plan in BillingPlanType.PAYMENT_PLANS
            and self.plan_expiration and self.plan_expiration > current_date
            and self.trial_end and self.trial_end > current_date
        )
        return r

    @property
    def is_free(self):
        return self.billing_plan == BillingPlanType.FREEMIUM

    @property
    def total_active_users(self) -> int:
        return self.active_users + self.tenants_active_users

    @property
    def is_blocked(self):
        return self.total_active_users > self.max_users

    def get_active_paid_templates(self, **kwargs):
        return self.template_set.active().paid()

    def get_user_ids(self, include_invited: bool = False) -> Set[int]:
        """ Return active and invited users in a current account"""
        user_ids = User.objects.on_account(self.id).values_list(
            'id',
            flat=True,
        )
        result = set(user_ids)
        if include_invited:
            invited_user_ids = UserInvite.objects.with_status(
                UserInviteStatus.PENDING,
            ).get_invited_users_in_account(account_id=self.id)
            result = result.union(invited_user_ids)
        return result

    def get_paid_users_count(self) -> int:

        if self.is_subscribed:
            return User.objects.filter(
                Q(
                    account_id=self.id,
                    status=UserStatus.ACTIVE
                )
                | Q(
                    account__lease_level=LeaseLevel.TENANT,
                    account__master_account_id=self.id,
                    status=UserStatus.ACTIVE
                )
            ).count()
        else:
            return User.objects.filter(
                account_id=self.id,
                status=UserStatus.ACTIVE
            ).count()

    @property
    def is_tenant(self):
        return self.lease_level == LeaseLevel.TENANT

    @property
    def ai_template_generations_limit_exceeded(self) -> bool:
        return (
            self.ai_templates_generations >= self.max_ai_templates_generations
        )

    @property
    def accounts_count(self) -> int:
        return self.tenants.only_tenants().count() + 1

    def __str__(self):
        return self.name


class AccountBaseMixin(models.Model):

    class Meta:
        abstract = True

    account = models.ForeignKey(Account, on_delete=models.CASCADE)


class AccountSignupData(
    AccountBaseMixin,
):

    utm_source = TruncatingCharField(max_length=32, null=True, blank=True)
    utm_medium = TruncatingCharField(max_length=32, null=True, blank=True)
    utm_campaign = TruncatingCharField(max_length=64, null=True, blank=True)
    utm_term = TruncatingCharField(max_length=128, null=True, blank=True)
    utm_content = TruncatingCharField(max_length=256, null=True, blank=True)
    gclid = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.account.name

    def as_dict(self):
        return {
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium,
            'utm_campaign': self.utm_campaign,
            'utm_term': self.utm_term,
            'utm_content': self.utm_content,
            'gclid': self.gclid
        }


class AccountSystemTemplate(
    SoftDeleteModel,
):

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    system_template = models.ForeignKey(
        'processes.SystemTemplate',
        on_delete=models.CASCADE
    )
    is_template_added = models.BooleanField(default=False)

    objects = BaseSoftDeleteManager.from_queryset(
        AccountSystemTemplateQuerySet
    )()


class UserInvite(
    SoftDeleteModel,
    AccountBaseMixin
):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = EmailLowerField()
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Should the user be admin (user\'s is_staff property)'
    )
    status = models.CharField(
        max_length=16,
        default=UserInviteStatus.PENDING,
        choices=UserInviteStatus.CHOICES
    )
    date_created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )
    date_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Last updated at'
    )
    invited_by = models.ForeignKey(
        'User',
        null=True,
        on_delete=models.SET_NULL,
        related_name='outcoming_invites'
    )
    invited_from = models.CharField(
        max_length=16,
        default=SourceType.EMAIL,
        choices=SourceType.CHOICES
    )
    invited_user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='incoming_invites',
        null=True,
    )

    objects = BaseSoftDeleteManager.from_queryset(UserInviteQuerySet)()

    class Meta:
        verbose_name = 'User Invite'
        constraints = [
            UniqueConstraint(
                fields=['account', 'invited_user'],
                condition=Q(is_deleted=False),
                name='accounts_userinvite_account_id_invited_user_id_unique',
            ),
        ]

    def __str__(self):
        return f'{self.account.name}: {self.email}'

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)


class User(AbstractUser, SoftDeleteModel):

    class Meta:
        verbose_name = 'User'
        constraints = [
            UniqueConstraint(
                fields=['email', 'account_id'],
                condition=(
                    Q(is_deleted=False)
                    & Q(type=UserType.GUEST)
                    & ~Q(status=UserStatus.INACTIVE)
                ),
                name='user_email_account_unique',
            ),
            UniqueConstraint(
                fields=['email'],
                condition=(
                    Q(is_deleted=False)
                    & Q(type=UserType.USER)
                    & Q(status=UserStatus.ACTIVE)
                ),
                name='user_email_unique',
            ),
        ]

    EMAIL_FIELD = 'some shit'  # need for build in password reset
    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = ['account_id']
    username = None

    email = EmailLowerField(blank=True)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='users',
    )
    phone = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )
    photo = models.URLField(max_length=1024, null=True, blank=True)
    status = models.CharField(
        choices=UserStatus.CHOICES,
        max_length=16,
        default=UserStatus.ACTIVE
    )
    type = models.CharField(
        choices=UserType.CHOICES,
        max_length=16,
        default=UserType.USER
    )
    language = models.CharField(
        choices=Language.CHOICES,
        max_length=10,
        default=settings.LANGUAGE_CODE
    )
    timezone = models.CharField(
        max_length=100,
        default=settings.TIME_ZONE,
        choices=Timezone.CHOICES,
    )
    date_fmt = models.CharField(
        choices=UserDateFormat.PY_CHOICES,
        max_length=20,
        default=UserDateFormat.PY_USA_12,
        verbose_name='Date format'
    )
    date_fdw = models.IntegerField(
        choices=UserFirstDayWeek.CHOICES,
        default=UserFirstDayWeek.SUNDAY,
        verbose_name='First day of the week'
    )
    is_admin = models.BooleanField(default=True)
    is_account_owner = models.BooleanField(default=False)

    notify_about_tasks = models.BooleanField(default=True)
    is_digest_subscriber = models.BooleanField(default=True)
    is_tasks_digest_subscriber = models.BooleanField(default=True)
    is_special_offers_subscriber = models.BooleanField(
        default=True,
        help_text='intercom emails'
    )
    is_newsletters_subscriber = models.BooleanField(
        default=True,
        help_text='customer.io emails'
    )
    is_new_tasks_subscriber = models.BooleanField(default=True)
    is_complete_tasks_subscriber = models.BooleanField(default=True)
    is_comments_mentions_subscriber = models.BooleanField(default=True)

    last_digest_send_time = models.DateTimeField(null=True)
    last_tasks_digest_send_time = models.DateTimeField(null=True)

    objects = SoftDeleteUserManager.from_queryset(UserQuerySet)()
    guests_objects = SoftDeleteGuestManager.from_queryset(GuestQuerySet)()
    include_inactive = BaseSoftDeleteManager.from_queryset(
        InactiveUserQuerySet
    )()

    search_content = SearchVectorField(null=True)

    def get_dynamic_mapping(self) -> Dict[str, str]:
        return {
            'account_name': self.account.name or '',
            'user_first_name': self.first_name,
            'user_last_name': self.last_name,
            'user_email': self.email,
        }

    def get_account_signup_data(self) -> AccountSignupData:
        return AccountSignupData.objects.get(
            account_id=self.account_id
        )

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def name_by_status(self):
        if self.status == UserStatus.INVITED:
            return f'{self.email} (invited user)'
        else:
            return self.name

    @property
    def company_name(self):
        return self.account.name

    @property
    def invite(self):
        return self.incoming_invites.filter(account=self.account).first()

    @property
    def status_invited(self) -> bool:
        return self.status == UserStatus.INVITED

    @property
    def is_guest(self) -> bool:
        return self.type == UserType.GUEST

    @property
    def is_user(self) -> bool:
        return self.type == UserType.USER

    def __str__(self):
        return self.name


class APIKey(
    SoftDeleteModel,
    AccountBaseMixin
):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='apikey'
    )
    key = models.CharField(max_length=32)
    name = models.CharField(max_length=200, blank=True)

    objects = BaseSoftDeleteManager.from_queryset(APIKeyQuerySet)()


class SystemMessage(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    publication_date = models.DateTimeField()
    is_delivery_completed = models.BooleanField(default=False)

    objects = Manager.from_queryset(SystemMessageQuerySet)()


class Notification(
    SoftDeleteModel,
    AccountBaseMixin
):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='author_notifications',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    text = models.TextField(null=True)
    type = models.CharField(max_length=24, choices=NotificationType.CHOICES)
    status = models.CharField(
        max_length=10,
        choices=NotificationStatus.CHOICES,
        default=NotificationStatus.NEW,
    )
    task = models.ForeignKey(
        'processes.Task',
        null=True,
        on_delete=models.CASCADE,
    )
    system_message = models.ForeignKey(
        SystemMessage,
        null=True,
        on_delete=models.CASCADE,
    )
    is_notified_about_not_read = models.BooleanField(
        default=False,
        help_text=(
            'True if the email '
            '"You have an unread notification" has been sent.'
        ),
    )
    datetime = models.DateTimeField(auto_now_add=True)

    objects = BaseSoftDeleteManager.from_queryset(
        NotificationsQuerySet
    )()


class Contact(
    SoftDeleteModel,
    AccountBaseMixin
):

    class Meta:
        ordering = ('first_name', 'last_name')

    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    photo = models.URLField(max_length=1024, null=True, blank=True)
    job_title = models.CharField(max_length=150, blank=True, null=True)
    source = models.CharField(
        max_length=255,
        choices=SourceType.CHOICES,
    )
    source_id = models.CharField(max_length=255)
    email = models.EmailField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    status = models.CharField(
        max_length=255,
        choices=UserStatus.CHOICES,
        default=UserStatus.ACTIVE
    )
    search_content = SearchVectorField(null=True)

    objects = BaseSoftDeleteManager.from_queryset(
        ContactQuerySet
    )()

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}' or self.email

    def __str__(self):
        return self.name


class UserGroup(
    SoftDeleteModel,
    AccountBaseMixin
):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=255)
    photo = models.URLField(max_length=1024, null=True, blank=True)
    users = models.ManyToManyField(User, related_name='user_groups')

    objects = BaseSoftDeleteManager.from_queryset(GroupQuerySet)()

    def __str__(self):
        return self.name
