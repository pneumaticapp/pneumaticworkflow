import { fileLinksIn } from '../core/files.js';
import { isRecord } from '../core/json.js';
import type { PeopleDirectory } from '../core/people.js';
import { BoundedJson, isoDate, type Json, type JsonObject } from './bounded.js';

const WORKFLOW_STATUSES: Record<number, string> = { 0: 'running', 1: 'done', 3: 'snoozed' };

const EVENT_TYPES: Record<number, string> = {
  0: 'run',
  1: 'complete',
  2: 'task_start',
  3: 'task_complete',
  4: 'task_revert',
  5: 'comment',
  6: 'ended',
  7: 'delay',
  8: 'revert',
  9: 'task_skip',
  10: 'ended_by_condition',
  11: 'urgent',
  12: 'not_urgent',
  13: 'task_skip_no_performers',
  14: 'task_performer_created',
  15: 'task_performer_deleted',
  16: 'force_resume',
  17: 'force_delay',
  18: 'due_date_changed',
  19: 'sub_workflow_run',
  20: 'task_performer_group_created',
  21: 'task_performer_group_deleted',
  22: 'task_delay',
  23: 'task_delegation',
};

export interface PresenterOptions {
  appUrl?: string;
  people?: PeopleDirectory;
}

export class PneumaticPresenter extends BoundedJson {
  constructor(private readonly options: PresenterOptions = {}) {
    super();
  }

  private link(data: JsonObject, path: string, id: Json | undefined) {
    if (this.options.appUrl && (typeof id === 'number' || typeof id === 'string')) {
      data.webUrl = `${this.options.appUrl}/${path}/${id}/`;
    }
  }

  private name(kind: 'user' | 'group', id: unknown, data: JsonObject, key: string) {
    const directory = kind === 'user' ? this.options.people?.users : this.options.people?.groups;
    const found = typeof id === 'number' ? directory?.get(id) : undefined;
    if (found) {
      data[key] = this.value(found);
    }
  }

  userName(id: unknown): Json {
    const found = typeof id === 'number' ? this.options.people?.users.get(id) : undefined;
    return found === undefined ? null : this.value(found);
  }

  selections(values: unknown): Json[] {
    return this.objects(values, (item) => (isRecord(item) ? this.value(item.value) : this.value(item)), 500);
  }

  fieldDefinition(value: unknown): JsonObject {
    const record = this.requireRecord(value);
    const data = this.pick(record, [
      'api_name',
      'name',
      'type',
      'is_required',
      'is_hidden',
      'description',
      'default',
      'dataset',
    ]);
    if (record.selections) {
      data.selections = this.selections(record.selections);
    }
    return data;
  }

  fieldValue(value: unknown): JsonObject {
    const record = this.requireRecord(value);
    const data = this.pick(record, ['api_name', 'name', 'type', 'is_required', 'is_hidden', 'description', 'value']);
    if (record.type === 'file') {
      data.fileLinks = typeof record.markdown_value === 'string' ? fileLinksIn(record.markdown_value) : [];
    }
    if (record.type === 'user') {
      Object.assign(data, this.pick(record, ['user_id', 'group_id']));
    }
    if (record.type === 'date' && typeof record.value === 'string' && record.value !== '') {
      data.date = isoDate(Number(record.value));
    }
    if (Array.isArray(record.selections) && record.selections.length) {
      data.selections = this.selections(record.selections);
    }
    return data;
  }

  fieldsets(values: unknown, field: (item: unknown) => Json): Json[] {
    return this.objects(values, (item) => {
      const record = this.requireRecord(item);
      const data = this.pick(record, ['api_name', 'name', 'title', 'description']);
      if (Array.isArray(record.rules) && record.rules.length) {
        data.rules = this.objects(record.rules, (rule) => this.pick(rule, ['type', 'value', 'fields']));
      }
      data.fields = this.objects(record.fields, field);
      return data;
    });
  }

  kickoffDefinition(kickoff: unknown): JsonObject {
    const record = isRecord(kickoff) ? kickoff : {};
    return {
      fields: this.objects(record.fields, (item) => this.fieldDefinition(item)),
      fieldsets: this.fieldsets(record.fieldsets, (item) => this.fieldDefinition(item)),
    };
  }

  performers(values: unknown): Json[] {
    return this.objects(values, (item) => {
      const record = this.requireRecord(item);
      const data = this.pick(record, ['type', 'source_id', 'is_completed', 'date_completed_tsp']);
      this.name(record.type === 'group' ? 'group' : 'user', record.source_id, data, 'name');
      return data;
    });
  }

  workflowStatus(status: unknown): Json {
    return typeof status === 'number' ? (WORKFLOW_STATUSES[status] ?? status) : this.value(status);
  }

  template(record: unknown): JsonObject {
    const data = this.pick(record, [
      'id',
      'name',
      'description',
      'is_active',
      'is_public',
      'tasks_count',
      'workflows_count',
      'is_editable',
    ]);
    this.link(data, 'templates', data.id);
    return data;
  }

  templateDetail(value: unknown): JsonObject {
    const record = this.requireRecord(value);
    const data = this.pick(
      record,
      [
        'id',
        'name',
        'description',
        'is_active',
        'is_public',
        'is_embedded',
        'public_url',
        'embed_url',
        'finalizable',
        'wf_name_template',
      ],
      ['description'],
    );
    this.link(data, 'templates', data.id);
    data.owners = this.objects(record.owners, (item) => this.pick(item, ['type', 'role', 'source_id']));
    data.kickoff = this.kickoffDefinition(record.kickoff);
    data.tasks = this.objects(record.tasks, (task) => this.templateStep(task));
    return data;
  }

  templateStep(value: unknown): JsonObject {
    const task = this.requireRecord(value);
    const step = this.pick(task, [
      'api_name',
      'name',
      'number',
      'description',
      'require_completion_by_all',
      'delay',
      'revert_task',
      'parents',
    ]);
    step.performers = this.objects(task.raw_performers, (item) => this.pick(item, ['type', 'source_id', 'label']));
    step.dueDate = isRecord(task.raw_due_date)
      ? this.pick(task.raw_due_date, ['rule', 'duration', 'duration_months', 'source_id'])
      : null;
    step.fields = this.objects(task.fields, (item) => this.fieldDefinition(item));
    step.fieldsets = this.fieldsets(task.fieldsets, (item) => this.fieldDefinition(item));
    step.checklists = this.objects(task.checklists, (item) => {
      const checklist = this.requireRecord(item);
      return { ...this.pick(checklist, ['api_name']), selections: this.selections(checklist.selections) };
    });
    step.conditions = this.objects(task.conditions, (item) => this.pick(item, ['action', 'rules']));
    return step;
  }

  currentTask(value: unknown): JsonObject {
    const record = this.requireRecord(value);
    const data = this.pick(record, [
      'id',
      'name',
      'api_name',
      'number',
      'status',
      'due_date_tsp',
      'date_started_tsp',
      'date_completed_tsp',
      'checklists_total',
      'checklists_marked',
    ]);
    data.performers = this.performers(record.performers);
    this.link(data, 'tasks', data.id);
    return data;
  }

  workflow(value: unknown, { isDetailed = false } = {}): JsonObject {
    const record = this.requireRecord(value);
    const data = this.pick(
      record,
      [
        'id',
        'name',
        'description',
        'is_urgent',
        'is_external',
        'finalizable',
        'due_date_tsp',
        'date_created_tsp',
        'date_completed_tsp',
        'workflow_starter',
        'ancestor_task_id',
        ...(isDetailed ? ['owners'] : []),
      ],
      ['description'],
    );
    data.status = this.workflowStatus(record.status);
    this.link(data, 'workflows', data.id);
    this.name('user', record.workflow_starter, data, 'workflowStarterName');
    if (Array.isArray(record.fields) && record.fields.length) {
      data.fields = this.objects(record.fields, (item) => this.fieldValue(item));
    }
    data.template = isRecord(record.template) ? this.pick(record.template, ['id', 'name', 'is_active']) : null;
    data.tasks = this.objects(record.tasks, (item) => this.currentTask(item));
    if (isDetailed) {
      const kickoff = isRecord(record.kickoff) ? record.kickoff : {};
      data.kickoff = this.objects(kickoff.output, (item) => this.fieldValue(item));
      data.kickoffFieldsets = this.fieldsets(kickoff.fieldsets, (item) => this.fieldValue(item));
    }
    return data;
  }

  task(record: unknown): JsonObject {
    const data = this.pick(record, [
      'id',
      'name',
      'api_name',
      'status',
      'workflow_name',
      'template_id',
      'is_urgent',
      'due_date_tsp',
      'date_started_tsp',
      'date_completed_tsp',
    ]);
    this.link(data, 'tasks', data.id);
    return data;
  }

  taskDetail(value: unknown): JsonObject {
    const record = this.requireRecord(value);
    const data = this.pick(
      record,
      [
        'id',
        'name',
        'api_name',
        'status',
        'description',
        'is_urgent',
        'require_completion_by_all',
        'due_date_tsp',
        'date_started_tsp',
        'date_completed_tsp',
        'checklists_total',
        'checklists_marked',
      ],
      ['description'],
    );
    this.link(data, 'tasks', data.id);
    if (isRecord(record.workflow)) {
      const workflow: JsonObject = {
        ...this.pick(record.workflow, ['id', 'name', 'template_name']),
        status: this.workflowStatus(record.workflow.status),
      };
      this.link(workflow, 'workflows', workflow.id);
      data.workflow = workflow;
    } else {
      data.workflow = null;
    }
    data.performers = this.performers(record.performers);
    data.output = this.objects(record.output, (item) => this.fieldValue(item));
    data.fieldsets = this.fieldsets(record.fieldsets, (item) => this.fieldValue(item));
    data.checklists = this.objects(record.checklists, (item) => this.checklist(item));
    data.revertTasks = this.objects(record.revert_tasks, (item) => this.pick(item, ['id', 'name', 'api_name']));
    data.subWorkflows = this.objects(record.sub_workflows, (item) => {
      const subWorkflow = this.requireRecord(item);
      return { ...this.pick(subWorkflow, ['id', 'name']), status: this.workflowStatus(subWorkflow.status) };
    });
    return data;
  }

  checklist(value: unknown): JsonObject {
    const record = this.requireRecord(value);
    return {
      ...this.pick(record, ['id', 'api_name']),
      selections: this.objects(record.selections, (item) => this.pick(item, ['id', 'value', 'is_selected'])),
    };
  }

  event(value: unknown): JsonObject {
    const record = this.requireRecord(value);
    const data = this.pick(
      record,
      ['id', 'created_tsp', 'updated_tsp', 'text', 'user_id', 'target_user_id', 'target_group_id', 'workflow_id'],
      ['text'],
    );
    data.type = typeof record.type === 'number' ? (EVENT_TYPES[record.type] ?? record.type) : this.value(record.type);
    data.task = isRecord(record.task) ? this.pick(record.task, ['id', 'name', 'number']) : null;
    this.name('user', record.user_id, data, 'userName');
    this.name('user', record.target_user_id, data, 'targetUserName');
    this.name('group', record.target_group_id, data, 'targetGroupName');
    if (record.status === 'deleted') {
      data.deleted = true;
    }
    if (isRecord(record.reactions) && Object.keys(record.reactions).length) {
      data.reactions = this.value(record.reactions);
    }
    return data;
  }

  highlight(value: unknown): JsonObject {
    const data = this.event(value);
    const { workflow } = this.requireRecord(value);
    if (isRecord(workflow)) {
      data.workflow = {
        ...this.pick(workflow, ['id', 'name']),
        status: this.workflowStatus(workflow.status),
        template: isRecord(workflow.template) ? this.pick(workflow.template, ['id', 'name']) : null,
      };
    }
    return data;
  }

  user(value: unknown, { isDetailed = false } = {}): JsonObject {
    const record = this.requireRecord(value);
    const data = this.pick(record, [
      'id',
      'email',
      'first_name',
      'last_name',
      'type',
      'status',
      'is_admin',
      'is_account_owner',
      'groups',
      ...(isDetailed ? ['timezone', 'language', 'manager_id', 'subordinates_ids'] : []),
    ]);
    if (isDetailed && isRecord(record.vacation)) {
      data.vacation = this.pick(record.vacation, ['absence_status', 'start_date', 'end_date', 'substitute_user_ids']);
    }
    return data;
  }

  group(record: unknown): JsonObject {
    return this.pick(record, ['id', 'name', 'type', 'users']);
  }

  attachment(record: unknown): JsonObject {
    return this.pick(record, ['id', 'file_id', 'url', 'access_type', 'source_type']);
  }
}
