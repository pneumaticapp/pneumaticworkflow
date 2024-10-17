from typing_extensions import Literal


class NotificationType:

    SYSTEM = 'system'
    COMMENT = 'comment'
    MENTION = 'mention'
    URGENT = 'urgent'
    NOT_URGENT = 'not_urgent'
    OVERDUE_TASK = 'overdue_task'
    DELAY_WORKFLOW = 'snooze_workflow'
    RESUME_WORKFLOW = 'resume_workflow'
    DUE_DATE_CHANGED = 'due_date_changed'
    REACTION = 'reaction'
    COMPLETE_TASK = 'complete_task'

    URGENT_TYPES = (
        URGENT,
        NOT_URGENT
    )

    CHOICES = (
        (SYSTEM, 'system'),
        (COMMENT, 'new comment'),
        (MENTION, 'mention'),
        (URGENT, 'urgent'),
        (NOT_URGENT, 'not urgent'),
        (OVERDUE_TASK, 'overdue task'),
        (DELAY_WORKFLOW, 'snooze workflow'),
        (RESUME_WORKFLOW, 'resume workflow'),
        (DUE_DATE_CHANGED, 'due date changed'),
        (REACTION, 'reaction'),
        (COMPLETE_TASK, 'complete task'),
    )


class NotificationStatus:
    NEW = 'new'
    READ = 'read'

    CHOICES = (
        (NEW, 'new'),
        (READ, 'read'),
    )


class UserStatus:

    INVITED = 'invited'
    ACTIVE = 'active'
    INACTIVE = 'inactive'

    CHOICES = (
        (INVITED, INVITED),
        (ACTIVE, ACTIVE),
        (INACTIVE, INACTIVE),
    )
    NOT_ACTIVE = {INVITED, INACTIVE}


class UserType:

    USER = 'user'
    GUEST = 'guest'

    CHOICES = (
        (USER, USER),
        (GUEST, GUEST),
    )
    LITERALS = Literal[USER, GUEST]


class UserFirstDayWeek:

    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

    CHOICES = (
        (SUNDAY, 'Sunday'),
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
        (SATURDAY, 'Saturday'),
    )


class UserDateFormat:

    PY_USA_12 = '%B %d, %Y, %I:%M%p'
    PY_EUROPE_12 = '%d %B, %Y, %I:%M%p'
    PY_USA_24 = '%B %d, %Y, %H:%M'
    PY_EUROPE_24 = '%d %B, %Y, %H:%M'

    API_USA_12 = 'MMM dd, yyy, p'
    API_EUROPE_12 = 'dd MMM, yyy, p'
    API_USA_24 = 'MMM dd, yyy, HH:mm'
    API_EUROPE_24 = 'dd MMM, yyy, HH:mm'

    TEXT_USA_12 = 'June 12, 2024, 06:00 PM'
    TEXT_EUROPE_12 = '12 June, 2024, 06:00 PM'
    TEXT_USA_24 = 'June 12, 2024, 18:00'
    TEXT_EUROPE_24 = '12 June, 2024, 18:00'

    API_CHOICES = (
        (API_USA_12, TEXT_USA_12),
        (API_EUROPE_12, TEXT_EUROPE_12),
        (API_USA_24, TEXT_USA_24),
        (API_EUROPE_24, TEXT_EUROPE_24),
    )

    PY_CHOICES = (
        (PY_USA_12, TEXT_USA_12),
        (PY_EUROPE_12, TEXT_EUROPE_12),
        (PY_USA_24, TEXT_USA_24),
        (PY_EUROPE_24, TEXT_EUROPE_24),
    )

    MAP_TO_PYTHON = {
        API_USA_12: PY_USA_12,
        API_EUROPE_12: PY_EUROPE_12,
        API_USA_24: PY_USA_24,
        API_EUROPE_24: PY_EUROPE_24,
    }

    MAP_TO_API = {
        PY_USA_12: API_USA_12,
        PY_EUROPE_12: API_EUROPE_12,
        PY_USA_24: API_USA_24,
        PY_EUROPE_24: API_EUROPE_24,
    }


class LeaseLevel:

    STANDARD = 'standard'
    PARTNER = 'partner'
    TENANT = 'tenant'

    CHOICES = (
        (STANDARD, STANDARD),
        (PARTNER, PARTNER),
        (TENANT, TENANT),
    )

    NOT_PARTNER_LEVELS = (STANDARD, TENANT)
    NOT_TENANT_LEVELS = (STANDARD, PARTNER)

    LITERALS = Literal[
        STANDARD,
        PARTNER,
        TENANT,
    ]


class BillingPlanType:

    FREEMIUM = 'free'
    PREMIUM = 'premium'
    FRACTIONALCOO = 'fractionalcoo'
    UNLIMITED = 'unlimited'

    CHOICES = (
        (FREEMIUM, FREEMIUM),
        (PREMIUM, PREMIUM),
        (FRACTIONALCOO, FRACTIONALCOO),
        (UNLIMITED, UNLIMITED),
    )

    LITERALS = Literal[
        FREEMIUM,
        PREMIUM,
        FRACTIONALCOO,
        UNLIMITED,
    ]

    PAYMENT_PLANS = {
        PREMIUM,
        FRACTIONALCOO,
        UNLIMITED,
    }


class InviteStatuses:

    VALID = 0
    INVALID = 2
    FILLNAME = 1


class SourceType:

    EMAIL = 'email'
    MICROSOFT = 'microsoft'
    GOOGLE = 'google'
    AUTH0 = 'auth0'

    CHOICES = (
        (EMAIL, EMAIL),
        (MICROSOFT, MICROSOFT),
        (GOOGLE, GOOGLE),
    )

    LITERALS = Literal[
        EMAIL,
        MICROSOFT,
        GOOGLE,
        AUTH0,
    ]


class UserInviteStatus:

    PENDING = 'pending'
    ACCEPTED = 'accepted'
    FAILED = 'failed'

    NOT_FAILED_STATUSES = {
        PENDING,
        ACCEPTED
    }

    CHOICES = (
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (FAILED, 'Failed'),
    )


class Timezone:

    UTC = 'UTC'
    UTC_8 = 'America/Anchorage'

    CHOICES = [
        ('Etc/GMT+12', '+12 Etc/GMT+12'),
        ('US/Samoa', '-11 US/Samoa'),
        ('Pacific/Honolulu', '-10 Pacific/Honolulu'),
        (UTC_8, '-08 America/Anchorage'),
        ('America/Los_Angeles', '-07 America/Los_Angeles'),
        ('America/Denver', '-06 America/Denver'),
        ('America/Chicago', '-05 America/Chicago'),
        ('America/New_York', '-04 America/New_York'),
        ('America/Caracas', '-04 America/Caracas'),
        ('America/Buenos_Aires', '-03 America/Buenos_Aires'),
        ('Atlantic/South_Georgia', '-02 Atlantic/South_Georgia'),
        ('Atlantic/Azores', '+00 Atlantic/Azores'),
        (UTC, '+00 UTC'),
        ('Europe/Berlin', '+02 Europe/Berlin'),
        ('Africa/Cairo', '+03 Africa/Cairo'),
        ('Europe/Moscow', '+03 Europe/Moscow'),
        ('Asia/Dubai', '+04 Asia/Dubai'),
        ('Asia/Karachi', '+05 Asia/Karachi'),
        ('Asia/Dhaka', '+06 Asia/Dhaka'),
        ('Asia/Bangkok', '+07 Asia/Bangkok'),
        ('Asia/Shanghai', '+08 Asia/Shanghai'),
        ('Asia/Tokyo', '+09 Asia/Tokyo'),
        ('Australia/Sydney', '+10 Australia/Sydney'),
        ('Pacific/Guadalcanal', '+11 Pacific/Guadalcanal'),
        ('Pacific/Fiji', '+12 Pacific/Fiji')
    ]


class Language:

    en = 'en'
    es = 'es'
    de = 'de'
    fr = 'fr'
    ru = 'ru'

    CHOICES = (
        (en, 'English'),
        (es, 'Spanish'),
        (de, 'German'),
        (fr, 'French'),
        (ru, 'Russian'),
    )

    EURO_CHOICES = (
        (en, 'English'),
        (es, 'Spanish'),
        (de, 'German'),
        (fr, 'French'),
    )

    LITERALS = Literal[en, es, de, fr, ru]
    VALUES = (en, es, de, fr, ru)
    EURO_VALUES = (en, es, de, fr)
