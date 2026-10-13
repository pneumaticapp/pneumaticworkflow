

class McpScope:
    READ = 'pneumatic:read'
    WRITE = 'pneumatic:write'
    FILE_READ = 'files:read'
    FILE_WRITE = 'files:write'

    CHOICES = (
        (READ, 'Read workflows, templates and tasks'),
        (WRITE, 'Run workflows, complete tasks and comment'),
        (FILE_READ, 'Read files and upload status'),
        (FILE_WRITE, 'Upload and import files'),
    )


class McpAudience:
    BACKEND = 'pneumatic-backend'
    FILES = 'pneumatic-files'


class McpTool:
    LIST_TEMPLATES = 'list_templates'
    GET_TEMPLATE = 'get_template'
    GET_TEMPLATE_KICKOFF = 'get_template_kickoff'
    LIST_WORKFLOWS = 'list_workflows'
    GET_WORKFLOW = 'get_workflow'
    GET_WORKFLOW_EVENTS = 'get_workflow_events'
    LIST_MY_TASKS = 'list_my_tasks'
    GET_TASK = 'get_task'
    LIST_ATTACHMENTS = 'list_attachments'
    GET_ATTACHMENT = 'get_attachment'
    RUN_WORKFLOW = 'run_workflow'
    COMPLETE_TASK = 'complete_task'
    COMMENT_TASK = 'comment_task'
    ADD_WORKFLOW_COMMENT = 'add_workflow_comment'
    CREATE_UPLOAD_LINK = 'create_upload_link'
    GET_UPLOAD_STATUS = 'get_upload_status'
    IMPORT_ATTACHMENT_FROM_URL = 'import_attachment_from_url'
    ATTACH_UPLOADED_FILE = 'attach_uploaded_file'
    GET_FILE_METADATA = 'get_file_metadata'
    CREATE_DOWNLOAD_TICKET = 'create_download_ticket'

    # Writes whose payload may reference stored files.
    FILE_LINK_WRITES = (
        RUN_WORKFLOW,
        COMPLETE_TASK,
        COMMENT_TASK,
        ADD_WORKFLOW_COMMENT,
    )
    FILE_SERVICE_TOOLS = (GET_FILE_METADATA, CREATE_DOWNLOAD_TICKET)


class HttpMethod:
    GET = 'GET'
    POST = 'POST'
    HEAD = 'HEAD'

    DELEGATION_CHOICES = (
        (GET, 'GET'),
        (POST, 'POST'),
    )
