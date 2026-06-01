import {
  ETemplateOwnerType,
  ETemplateOwnerRole,
  ETaskPerformerType,
  ITemplateResponse,
  ITemplate,
  EExtraFieldType,
  IFieldsetData,
} from '../../types/template';
import { ESubscriptionPlan } from '../../types/account';
import { TUserListItem, EUserStatus } from '../../types/user';
import { getNormalizedTemplate, mapTemplateRequest, getEmptyKickoff, cleanTemplateReferences, collectFieldApiNames } from '../template';
import { EConditionAction, EConditionOperators, EConditionLogicOperations, TConditionRule } from '../../components/TemplateEdit/TaskForm/Conditions/types';
import { makeExtraField } from '../../__stubs__/fields.factory';
import { makeFieldsetData } from '../../__stubs__/fieldsets.factory';

const emptyFieldsetsMap: ReadonlyMap<string, IFieldsetData> = new Map();

const createMockUser = (overrides: Partial<TUserListItem> = {}): TUserListItem => ({
  id: 1,
  email: 'user@example.com',
  firstName: 'Test',
  lastName: 'User',
  phone: '',
  photo: '',
  status: EUserStatus.Active,
  type: 'user',
  isAdmin: false,
  isAccountOwner: false,
  ...overrides,
});

const createMockTemplateResponse = (
  overrides: Partial<ITemplateResponse> = {},
): ITemplateResponse => ({
  id: 1,
  name: 'Test Template',
  description: 'Test description',
  isActive: true,
  finalizable: true,
  dateUpdated: '2024-01-01T00:00:00Z',
  updatedBy: 1,
  owners: [
    {
      apiName: 'owner-123456',
      sourceId: '1',
      type: ETemplateOwnerType.User,
      role: ETemplateOwnerRole.Owner,
    },
  ],
  kickoff: {
    description: '',
    fields: [],
    fieldsets: [],
  },
  tasks: [
    {
      id: 1,
      name: 'Task 1',
      number: 1,
      description: '',
      requireCompletionByAll: false,
      skipForStarter: false,
      delay: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      rawPerformers: [
        {
          sourceId: '1',
          type: ETaskPerformerType.User,
          label: 'Test User',
          apiName: 'raw-performer-123456',
        },
      ],
      checklists: [],
      revertTask: null,
      ancestors: [],
      fieldsets: [],
    },
  ],
  isPublic: false,
  publicUrl: null,
  publicSuccessUrl: null,
  isEmbedded: false,
  embedUrl: null,
  wfNameTemplate: null,
  completionNotification: false,
  reminderNotification: false,
  ...overrides,
});

const createMockTemplate = (overrides: Partial<ITemplate> = {}): ITemplate => ({
  id: 1,
  name: 'Test Template',
  description: 'Test description',
  isActive: true,
  finalizable: true,
  dateUpdated: '2024-01-01T00:00:00Z',
  updatedBy: 1,
  owners: [
    {
      apiName: 'owner-123456',
      sourceId: '1',
      type: ETemplateOwnerType.User,
      role: ETemplateOwnerRole.Owner,
    },
  ],
  kickoff: getEmptyKickoff(),
  tasks: [
    {
      id: 1,
      apiName: 'task-123456',
      number: 1,
      name: 'Task 1',
      description: '',
      delay: null,
      rawDueDate: {
        apiName: 'due-date-123456',
        duration: null,
        durationMonths: null,
        rulePreposition: 'after',
        ruleTarget: null,
        sourceId: null,
      },
      requireCompletionByAll: false,
      skipForStarter: false,
      rawPerformers: [
        {
          sourceId: '1',
          type: ETaskPerformerType.User,
          label: 'Test User',
          apiName: 'raw-performer-123456',
        },
      ],
      fields: [],
      uuid: 'test-uuid',
      conditions: [],
      checklists: [],
      revertTask: null,
      ancestors: [],
      fieldsets: [],
    },
  ],
  isPublic: false,
  publicUrl: null,
  publicSuccessUrl: null,
  isEmbedded: false,
  embedUrl: null,
  wfNameTemplate: null,
  tasksCount: 1,
  performersCount: 1,
  completionNotification: false,
  reminderNotification: false,
  ...overrides,
});

describe('template utilities', () => {
  describe('getEmptyKickoff', () => {
    it('returns empty kickoff object', () => {
      const kickoff = getEmptyKickoff();

      expect(kickoff).toEqual({
        description: '',
        fields: [],
        fieldsets: [],
      });
    });
  });

  describe('getNormalizedTemplate', () => {
    const mockUsers: TUserListItem[] = [createMockUser({ id: 1 }), createMockUser({ id: 2 })];

    it('normalizes template with only owners', () => {
      const templateResponse = createMockTemplateResponse();

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      const ownerRoles = result.owners.map(o => o.role);
      expect(ownerRoles).toEqual([ETemplateOwnerRole.Owner]);
    });

    it('normalizes template with viewers in owners', () => {
      const owners = [
        {
          apiName: 'owner-123456',
          sourceId: '1',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Owner,
        },
        {
          apiName: 'viewer-123456',
          sourceId: '1',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Viewer,
        },
        {
          apiName: 'viewer-789012',
          sourceId: '2',
          type: ETemplateOwnerType.UserGroup,
          role: ETemplateOwnerRole.Viewer,
        },
      ];
      const templateResponse = createMockTemplateResponse({ owners });

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.owners).toEqual(owners);
      const viewers = result.owners.filter(o => o.role === ETemplateOwnerRole.Viewer);
      expect(viewers).toHaveLength(2);
    });

    it('normalizes template with starters in owners', () => {
      const owners = [
        {
          apiName: 'owner-123456',
          sourceId: '1',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Owner,
        },
        {
          apiName: 'starter-123456',
          sourceId: '1',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Starter,
        },
        {
          apiName: 'starter-789012',
          sourceId: '3',
          type: ETemplateOwnerType.UserGroup,
          role: ETemplateOwnerRole.Starter,
        },
      ];
      const templateResponse = createMockTemplateResponse({ owners });

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      const starters = result.owners.filter(o => o.role === ETemplateOwnerRole.Starter);
      expect(starters).toHaveLength(2);
    });

    it('normalizes template with all roles in owners', () => {
      const owners = [
        {
          apiName: 'owner-123456',
          sourceId: '1',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Owner,
        },
        {
          apiName: 'viewer-123456',
          sourceId: '1',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Viewer,
        },
        {
          apiName: 'starter-123456',
          sourceId: '2',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Starter,
        },
      ];
      const templateResponse = createMockTemplateResponse({ owners });

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.owners).toEqual(owners);
      const viewers = result.owners.filter(o => o.role === ETemplateOwnerRole.Viewer);
      const starters = result.owners.filter(o => o.role === ETemplateOwnerRole.Starter);
      expect(viewers).toHaveLength(1);
      expect(starters).toHaveLength(1);
    });

    it('calculates tasksCount correctly', () => {
      const templateResponse = createMockTemplateResponse();

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.tasksCount).toBe(1);
    });

    it('calculates performersCount correctly', () => {
      const templateResponse = createMockTemplateResponse();

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.performersCount).toBe(1);
    });
  });

  describe('mapTemplateRequest', () => {
    it('maps template with owners of different roles', () => {
      const owners = [
        {
          apiName: 'owner-123456',
          sourceId: '1',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Owner,
        },
        {
          apiName: 'viewer-123456',
          sourceId: '1',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Viewer,
        },
        {
          apiName: 'starter-123456',
          sourceId: '2',
          type: ETemplateOwnerType.User,
          role: ETemplateOwnerRole.Starter,
        },
      ];
      const template = createMockTemplate({ owners });

      const result = mapTemplateRequest(template, emptyFieldsetsMap);

      expect(result.owners).toEqual(owners);
    });

    it('preserves template name', () => {
      const template = createMockTemplate({ name: 'Custom Template Name' });

      const result = mapTemplateRequest(template, emptyFieldsetsMap);

      expect(result.name).toBe('Custom Template Name');
    });

    it('uses default name when template name is empty', () => {
      const template = createMockTemplate({ name: '' });

      const result = mapTemplateRequest(template, emptyFieldsetsMap);

      expect(result.name).toBe('New Template');
    });

    it('preserves publicSuccessUrl', () => {
      const template = createMockTemplate({ publicSuccessUrl: 'https://example.com/success' });

      const result = mapTemplateRequest(template, emptyFieldsetsMap);

      expect(result.publicSuccessUrl).toBe('https://example.com/success');
    });

    it('sets publicSuccessUrl to null when empty', () => {
      const template = createMockTemplate({ publicSuccessUrl: '' });

      const result = mapTemplateRequest(template, emptyFieldsetsMap);

      expect(result.publicSuccessUrl).toBeNull();
    });
  describe('cleanTemplateReferences', () => {
    it('removes invalid field references from template and task text fields but preserves system vars', () => {
      const template = createMockTemplate({
        wfNameTemplate: 'Name: {{valid-field}} and {{invalid-field}} and {{template-name}}',
        kickoff: {
          ...getEmptyKickoff(),
          fields: [makeExtraField({ apiName: 'valid-field', type: EExtraFieldType.Text, name: 'Valid Field', order: 1 })],
        },
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            name: 'Task {{invalid-field}} and {{valid-field}}',
            description: 'Desc {{workflow-starter}} and {{invalid-field}}',
            number: 1,
            fields: [makeExtraField({ apiName: 'valid-task-field', type: EExtraFieldType.Text, name: 'Valid Task Field', order: 1 })],
          },
          {
            ...createMockTemplate().tasks[0],
            name: 'Task 2 {{valid-field}} and {{valid-task-field}} and {{broken}}',
            description: 'Desc',
            number: 2,
          },
        ],
      });

      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);

      // wfNameTemplate: {{template-name}} is a WF_NAME system var, preserved; {{invalid-field}} removed
      expect(cleaned.wfNameTemplate).toBe('Name: {{valid-field}} and  and {{template-name}}');
      expect(cleaned.tasks[0].name).toBe('Task  and {{valid-field}}');
      // {{workflow-starter}} is a TASK system var, preserved; {{invalid-field}} removed
      expect(cleaned.tasks[0].description).toBe('Desc {{workflow-starter}} and ');
      // Task 2 variables should successfully retain valid fields from kickoff and task 1
      expect(cleaned.tasks[1].name).toBe('Task 2 {{valid-field}} and {{valid-task-field}} and ');
    });

    it('preserves kickoff fieldset field references in wfNameTemplate', () => {
      const fieldsetFields = [
        makeExtraField({ apiName: 'fieldset-field-1', type: EExtraFieldType.Text, name: 'Fieldset Field 1', order: 1 }),
        makeExtraField({ apiName: 'fieldset-field-2', type: EExtraFieldType.Text, name: 'Fieldset Field 2', order: 2 }),
      ];
      const fieldsetsMap = new Map<string, IFieldsetData>([
        ['my-fieldset', makeFieldsetData({ apiName: 'my-fieldset', name: 'My Fieldset', fields: fieldsetFields })],
      ]);

      const template = createMockTemplate({
        wfNameTemplate: 'Name: {{direct-field}} and {{fieldset-field-1}} and {{fieldset-field-2}} and {{invalid-field}} and {{date}}',
        kickoff: {
          ...getEmptyKickoff(),
          fields: [makeExtraField({ apiName: 'direct-field', type: EExtraFieldType.Text, name: 'Direct', order: 1 })],
          fieldsets: [{ apiName: 'my-fieldset', order: 1 }],
        },
      });

      const cleaned = cleanTemplateReferences(template, fieldsetsMap);

      expect(cleaned.wfNameTemplate).toBe('Name: {{direct-field}} and {{fieldset-field-1}} and {{fieldset-field-2}} and  and {{date}}');
    });

    it('removes invalid field references from conditions', () => {
      const template = createMockTemplate({
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            conditions: [
              {
                apiName: 'cond-1',
                order: 1,
                action: EConditionAction.StartTask,
                rules: [
                  { field: 'valid-field', operator: EConditionOperators.Equal, logicOperation: EConditionLogicOperations.And, predicateApiName: '1' } as unknown as TConditionRule,
                  { field: 'invalid-field', operator: EConditionOperators.Equal, logicOperation: EConditionLogicOperations.And, predicateApiName: '2' } as unknown as TConditionRule,
                ],
              },
            ],
          },
        ],
        kickoff: {
          ...getEmptyKickoff(),
          fields: [makeExtraField({ apiName: 'valid-field', type: EExtraFieldType.Text, name: 'Valid', order: 1 })],
        },
      });

      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);
      const rules = cleaned.tasks[0].conditions[0].rules;
      expect(rules).toHaveLength(1);
      expect(rules[0].field).toBe('valid-field');
    });

    it('allows task name to become empty if all variables are invalid', () => {
      const template = createMockTemplate({
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            number: 2,
            name: '{{invalid-field}}',
          },
        ],
      });
      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);
      expect(cleaned.tasks[0].name).toBe('');
    });

    it('safely handles empty rawPerformers array or invalid field performers and preserves valid members', () => {
      const template = createMockTemplate({
        kickoff: {
          ...getEmptyKickoff(),
          fields: [makeExtraField({ apiName: 'valid-user-field', type: EExtraFieldType.User, name: 'Valid User', order: 1 })],
        },
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            rawPerformers: [
              { type: ETaskPerformerType.OutputUser, sourceId: 'invalid-field', label: 'Broken', apiName: '1' },
              { type: ETaskPerformerType.OutputUser, sourceId: 'valid-user-field', label: 'Valid User', apiName: '2' },
              { type: ETaskPerformerType.User, sourceId: '1', label: 'Regular User', apiName: '3' },
            ],
          },
        ],
      });
      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);
      expect(cleaned.tasks[0].rawPerformers).toHaveLength(2);
      expect(cleaned.tasks[0].rawPerformers.map((p) => p.apiName)).toEqual(['2', '3']);
    });

    it('removes invalid field references from rawDueDate', () => {
      const template = createMockTemplate({
        kickoff: {
          ...getEmptyKickoff(),
          fields: [makeExtraField({ apiName: 'valid-date-field', type: EExtraFieldType.Date, name: 'Valid Date', order: 1 })],
        },
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            number: 1,
            rawDueDate: {
              apiName: 'due-1', duration: null, durationMonths: null, rulePreposition: 'after', ruleTarget: 'field', sourceId: 'valid-date-field',
            },
          },
          {
            ...createMockTemplate().tasks[0],
            number: 2,
            rawDueDate: {
              apiName: 'due-2', duration: null, durationMonths: null, rulePreposition: 'after', ruleTarget: 'field', sourceId: 'invalid-field',
            },
          },
        ]
      });
      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);
      expect(cleaned.tasks[0].rawDueDate?.sourceId).toBe('valid-date-field');
      expect(cleaned.tasks[0].rawDueDate?.ruleTarget).toBe('field');
      expect(cleaned.tasks[1].rawDueDate?.duration).toBeNull();
      expect(cleaned.tasks[1].rawDueDate?.durationMonths).toBeNull();
      expect(cleaned.tasks[1].rawDueDate?.sourceId).toBeNull();
      expect(cleaned.tasks[1].rawDueDate?.ruleTarget).toBe('task started');
    });
    it('preserves Start After condition rules and handles empty fields', () => {
      const template = createMockTemplate({
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            conditions: [
              {
                apiName: 'cond-1',
                order: 1,
                action: EConditionAction.StartTask,
                rules: [
                  { field: 'task-123', fieldType: 'task', operator: EConditionOperators.Equal, logicOperation: EConditionLogicOperations.And, predicateApiName: '1' } as unknown as TConditionRule,
                  { field: '', operator: EConditionOperators.Equal, logicOperation: EConditionLogicOperations.And, predicateApiName: '2' } as unknown as TConditionRule,
                  { field: undefined, operator: EConditionOperators.Equal, logicOperation: EConditionLogicOperations.And, predicateApiName: '3' } as unknown as TConditionRule,
                  { field: null, operator: EConditionOperators.Equal, logicOperation: EConditionLogicOperations.And, predicateApiName: '4' } as unknown as TConditionRule,
                  { field: 'invalid-field', fieldType: 'field', operator: EConditionOperators.Equal, logicOperation: EConditionLogicOperations.And, predicateApiName: '5' } as unknown as TConditionRule,
                ],
              },
            ],
          },
        ],
      });

      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);
      const rules = cleaned.tasks[0].conditions[0].rules;
      
      expect(rules).toHaveLength(4);
      expect(rules[0].field).toBe('task-123');
      expect(rules[1].field).toBe('');
      expect(rules[2].field).toBeUndefined();
      expect(rules[3].field).toBeNull();
    });

    it('removes Manager performer when source step is deleted from template', () => {
      const template = createMockTemplate({
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            apiName: 'task-1',
            number: 1,
            rawPerformers: [
              { type: ETaskPerformerType.Manager, sourceId: 'task-deleted', label: 'Manager: Deleted', apiName: 'perf-mgr-1' },
              { type: ETaskPerformerType.User, sourceId: '1', label: 'Regular User', apiName: 'perf-user-1' },
            ],
          },
        ],
      });

      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);

      expect(cleaned.tasks[0].rawPerformers).toHaveLength(1);
      expect(cleaned.tasks[0].rawPerformers[0].type).toBe(ETaskPerformerType.User);
    });

    it('preserves Manager performer when source step exists in template', () => {
      const baseTask = createMockTemplate().tasks[0];
      const template = createMockTemplate({
        tasks: [
          { ...baseTask, apiName: 'task-1', number: 1 },
          {
            ...baseTask,
            apiName: 'task-2',
            number: 2,
            rawPerformers: [
              { type: ETaskPerformerType.Manager, sourceId: 'task-1', label: 'Manager: Task 1', apiName: 'perf-mgr-1' },
            ],
          },
        ],
      });

      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);

      expect(cleaned.tasks[1].rawPerformers).toHaveLength(1);
      expect(cleaned.tasks[1].rawPerformers[0].type).toBe(ETaskPerformerType.Manager);
      expect(cleaned.tasks[1].rawPerformers[0].sourceId).toBe('task-1');
    });

    it('removes Manager performer with empty sourceId', () => {
      const template = createMockTemplate({
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            rawPerformers: [
              { type: ETaskPerformerType.Manager, sourceId: '', label: 'Manager: ?', apiName: 'perf-mgr-empty' },
              { type: ETaskPerformerType.Manager, sourceId: null, label: 'Manager: null', apiName: 'perf-mgr-null' },
            ],
          },
        ],
      });

      const cleaned = cleanTemplateReferences(template, emptyFieldsetsMap);

      expect(cleaned.tasks[0].rawPerformers).toHaveLength(0);
    });
  });
});

  describe('collectFieldApiNames', () => {
    it('does not crash and leaves Set empty for empty fields and fieldsets', () => {
      const validApiNames = new Set<string>();

      collectFieldApiNames([], [], emptyFieldsetsMap, validApiNames);

      expect(validApiNames.size).toBe(0);
    });

    it('collects apiNames from direct fields and fieldset fields', () => {
      const fields = [
        makeExtraField({ apiName: 'direct-field', type: EExtraFieldType.Text, name: 'Direct' }),
      ];
      const fieldsets = [{ apiName: 'my-fs', order: 0 }];
      const fieldsetsMap = new Map<string, IFieldsetData>([
        ['my-fs', makeFieldsetData({
          apiName: 'my-fs', name: 'FS',
          fields: [
            makeExtraField({ apiName: 'fs-field-1', name: 'F1' }),
            makeExtraField({ apiName: 'fs-field-2', type: EExtraFieldType.Number, name: 'F2', order: 1 }),
          ],
        })],
      ]);
      const validApiNames = new Set<string>();

      collectFieldApiNames(fields, fieldsets, fieldsetsMap, validApiNames);

      expect(validApiNames.has('direct-field')).toBe(true);
      expect(validApiNames.has('fs-field-1')).toBe(true);
      expect(validApiNames.has('fs-field-2')).toBe(true);
      expect(validApiNames.size).toBe(3);
    });

    it('ignores fieldset missing from catalog without crashing', () => {
      const fieldsets = [{ apiName: 'non-existent-fs', order: 0 }];
      const validApiNames = new Set<string>();

      collectFieldApiNames([], fieldsets, emptyFieldsetsMap, validApiNames);

      expect(validApiNames.size).toBe(0);
    });
  });
});
