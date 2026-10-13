from typing_extensions import Literal


class SourceType:
    """
    File source types.
    Defines which entity the file is attached to.
    """
    ACCOUNT = 'Account'
    WORKFLOW = 'Workflow'
    TASK = 'Task'
    TEMPLATE = 'Template'

    CHOICES = (
        (ACCOUNT, 'Account'),
        (WORKFLOW, 'Workflow'),
        (TASK, 'Task'),
        (TEMPLATE, 'Template'),
    )
    LITERALS = Literal['Account', 'Workflow', 'Task', 'Template']


class AccessType:
    """
    File access types.
    PUBLIC - accessible to everyone
    ACCOUNT - accessible to all account users
    RESTRICTED - accessible only to specified users/groups
    """
    PUBLIC = 'public'
    ACCOUNT = 'account'
    RESTRICTED = 'restricted'

    CHOICES = (
        (PUBLIC, 'Public'),
        (ACCOUNT, 'Account'),
        (RESTRICTED, 'Restricted'),
    )
    LITERALS = Literal['public', 'account', 'restricted']


class UploadTargetType:
    TASK = 'task'
    KICKOFF = 'kickoff'

    CHOICES = (
        (TASK, 'Task'),
        (KICKOFF, 'Kickoff'),
    )
    LITERALS = Literal['task', 'kickoff']


class UploadStatus:
    PENDING = 'pending'
    IMPORTING = 'importing'
    READY = 'ready'
    ATTACHED = 'attached'
    FAILED = 'failed'
    CLEANED = 'cleaned'

    # Computed for API responses only, never stored.
    EXPIRED = 'expired'
    REVOKED = 'revoked'

    CHOICES = (
        (PENDING, 'Pending'),
        (IMPORTING, 'Importing'),
        (READY, 'Ready'),
        (ATTACHED, 'Attached'),
        (FAILED, 'Failed'),
        (CLEANED, 'Cleaned'),
    )
    # Sessions that still accept an upload capability.
    OPEN = (PENDING, IMPORTING, READY)
    # Sessions whose source URL is no longer needed.
    FINISHED = (READY, ATTACHED, FAILED, CLEANED)


class ImportJobState:
    QUEUED = 'queued'
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'

    CHOICES = (
        (QUEUED, 'Queued'),
        (RUNNING, 'Running'),
        (DONE, 'Done'),
        (FAILED, 'Failed'),
    )
    ACTIVE = (QUEUED, RUNNING)
    FINISHED = (DONE, FAILED)


class FileOperation:
    UPLOAD = 'upload'
    IMPORT = 'import'
    DOWNLOAD = 'download'
    METADATA = 'metadata'

    CHOICES = (
        (UPLOAD, 'Upload'),
        (IMPORT, 'Import'),
        (DOWNLOAD, 'Download'),
        (METADATA, 'Metadata'),
    )
    CAPABILITY_OPERATIONS = (UPLOAD, IMPORT)
