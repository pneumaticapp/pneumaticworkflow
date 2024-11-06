

class AccountAnalyticsEvent:
    verified = 'Account Verified'
    created = 'Account Created'
    webhooks_subscribed = 'Account Webhooks Subscribed'


class TenantsAnalyticsEvent:
    added = 'Tenant Added'
    accessed = 'Tenant Accessed'


class UserAnalyticsEvent:
    invite_accepted = 'Invite Accepted'
    invited = 'User Invited'
    invite_sent = 'Invite Sent'
    joined = 'User Joined'
    digest = 'User Unsubscribed From Digest'
    logged_in = 'User Logged In'
    transferred = 'User Transferred'
    guest_invited = 'Guest Invited'
    guest_invite_sent = 'Guest Invite Sent'


class TemplateAnalyticsEvent:
    created = 'Template Created'
    updated = 'Template Updated'
    deleted = 'Template Deleted'
    integrated = 'Template Integrated'
    kickoff_created = 'Template Kickoff Created'
    kickoff_edited = 'Template Kickoff Edited'
    condition_created = 'Task Condition Created'
    checklist_created = 'Task Checklist Created'
    due_date_created = 'Task "Due In" Created'
    generation_init = 'Template generation initialized'
    generated_from_landing = 'Template generated from landing'
    created_from_landing_library = 'Template created from landing library'


class LibraryTemplateAnalyticsEvent:

    opened = 'Library Template Opened'


class WorkflowAnalyticsEvent:
    started = 'Workflow Started'
    completed = 'Workflow Completed'
    ended = 'Workflow Ended'
    terminated = 'Workflow Terminated'
    returned = 'Workflow returned'
    updated = 'Workflow Updated'
    urgent = 'Urgent workflow'
    delayed = 'Workflow snoozed'


class TaskAnalyticsEvent:
    completed = 'Task Completed'
    returned = 'Task Returned'


class CommentAnalyticsEvent:
    added = 'Comment Added'
    edited = 'Comment Edited'
    deleted = 'Comment Deleted'
    reaction_added = 'Reaction added'
    reaction_deleted = 'Reaction deleted'


class SubscriptionAnalyticsEvent:
    trial = 'Trial Subscription Created'
    converted = 'Trial Subscription Converted'
    created = 'Subscription Created'
    canceled = 'Subscription Canceled'
    expired = 'Subscription Expired'
    updated = 'Subscription Updated'


class SearchAnalyticsEvent:
    search = 'Search'


class MentionsAnalyticsEvent:
    created = 'Mention Created'


class EventCategory:
    tasks = 'Tasks'
    templates = 'Templates'
    workflows = 'Workflows'
    users = 'Users'
    accounts = 'Accounts'
    comments = 'Comments'
    subscriptions = 'Subscriptions'
    attachments = 'Attachments'
    search = 'Search'
    mentions = 'Mentions'
    tenants = 'Tenants'


class AttachmentAnalyticsEvent:
    uploaded = 'File Uploaded'
