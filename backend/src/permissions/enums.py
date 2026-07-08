class PermissionSource:
    """Source that granted a permission.

    Every permission row tracks *why* it was granted so it can be
    surgically revoked when that source is removed (e.g. comment deleted,
    performer removed) without a full recalculation.

    ``source_id`` references the PK of the model identified by this enum.
    """

    PERFORMER = 'Performer'
    PERFORMER_GROUP = 'PerformerGroup'
    MENTION = 'Mention'
    TEMPLATE_OWNER = 'TemplateOwner'
    WORKFLOW_VIEWER = 'WorkflowViewer'
    VACATION = 'Vacation'

    CHOICES = (
        (PERFORMER, 'Performer'),
        (PERFORMER_GROUP, 'Performer Group'),
        (MENTION, 'Mention'),
        (TEMPLATE_OWNER, 'Template Owner'),
        (WORKFLOW_VIEWER, 'Workflow Viewer'),
        (VACATION, 'Vacation substitute'),
    )

