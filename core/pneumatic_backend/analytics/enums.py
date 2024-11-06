

class MailoutType:

    """ Сlass maps user subscription settings and mailout from customer.io """

    NEWSLETTER = 0
    OFFER = 1
    COMMENTS = 2
    NEW_TASK = 3
    WF_DIGEST = 4
    TASKS_DIGEST = 5
    COMPLETE_TASK = 6

    CHOICES = (
        (NEWSLETTER, 'Newsletter'),
        (OFFER, 'Special offers'),
        (COMMENTS, 'Comments and Mentions'),
        (NEW_TASK, 'New tasks'),
        (WF_DIGEST, 'Workflows Weekly Digest'),
        (TASKS_DIGEST, 'Tasks Weekly Digest'),
        (COMPLETE_TASK, 'Complete task'),
    )

    MAP = {
        NEWSLETTER: 'is_newsletters_subscriber',
        OFFER: 'is_special_offers_subscriber',
        COMMENTS: 'is_comments_mentions_subscriber',
        NEW_TASK: 'is_new_tasks_subscriber',
        WF_DIGEST: 'is_digest_subscriber',
        TASKS_DIGEST: 'is_tasks_digest_subscriber',
        COMPLETE_TASK: 'is_complete_tasks_subscriber',
    }

    CUSTOMERIO_TYPES = {
        NEWSLETTER
    }
