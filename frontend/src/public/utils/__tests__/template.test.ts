import {
  ETemplateOwnerType,
  ETemplateOwnerRole,
  ETaskPerformerType,
  ITemplateResponse,
  ITemplate,
  EExtraFieldType,
  IExtraField,
} from '../../types/template';
import { ESubscriptionPlan } from '../../types/account';
import { TUserListItem, EUserStatus } from '../../types/user';
import { getNormalizedTemplate, mapTemplateRequest, getEmptyKickoff, cleanTemplateReferences } from '../template';
import { EConditionAction, EConditionOperators, EConditionLogicOperations, TConditionRule } from '../../components/TemplateEdit/TaskForm/Conditions/types';

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

      const result = mapTemplateRequest(template);

      expect(result.owners).toEqual(owners);
    });

    it('preserves template name', () => {
      const template = createMockTemplate({ name: 'Custom Template Name' });

      const result = mapTemplateRequest(template);

      expect(result.name).toBe('Custom Template Name');
    });

    it('uses default name when template name is empty', () => {
      const template = createMockTemplate({ name: '' });

      const result = mapTemplateRequest(template);

      expect(result.name).toBe('New Template');
    });

    it('preserves publicSuccessUrl', () => {
      const template = createMockTemplate({ publicSuccessUrl: 'https://example.com/success' });

      const result = mapTemplateRequest(template);

      expect(result.publicSuccessUrl).toBe('https://example.com/success');
    });

    it('sets publicSuccessUrl to null when empty', () => {
      const template = createMockTemplate({ publicSuccessUrl: '' });

      const result = mapTemplateRequest(template);

      expect(result.publicSuccessUrl).toBeNull();
    });
  describe('cleanTemplateReferences', () => {
    it('removes invalid field references from template and task text fields but preserves system vars', () => {
      const template = createMockTemplate({
        wfNameTemplate: 'Name: {{valid-field}} and {{invalid-field}} and {{template-name}}',
        kickoff: {
          ...getEmptyKickoff(),
          fields: [{ apiName: 'valid-field', type: EExtraFieldType.Text, name: 'Valid Field', order: 1 } as unknown as IExtraField],
        },
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            name: 'Task {{invalid-field}} and {{valid-field}}',
            description: 'Desc {{workflow-starter}} and {{invalid-field}}',
            number: 1,
            fields: [{ apiName: 'valid-task-field', type: EExtraFieldType.Text, name: 'Valid Task Field', order: 1 } as unknown as IExtraField],
          },
          {
            ...createMockTemplate().tasks[0],
            name: 'Task 2 {{valid-field}} and {{valid-task-field}} and {{broken}}',
            description: 'Desc',
            number: 2,
          },
        ],
      });

      const cleaned = cleanTemplateReferences(template);

      // wfNameTemplate: {{template-name}} is a WF_NAME system var, preserved; {{invalid-field}} removed
      expect(cleaned.wfNameTemplate).toBe('Name: {{valid-field}} and  and {{template-name}}');
      expect(cleaned.tasks[0].name).toBe('Task  and {{valid-field}}');
      // {{workflow-starter}} is a TASK system var, preserved; {{invalid-field}} removed
      expect(cleaned.tasks[0].description).toBe('Desc {{workflow-starter}} and');
      // Task 2 variables should successfully retain valid fields from kickoff and task 1
      expect(cleaned.tasks[1].name).toBe('Task 2 {{valid-field}} and {{valid-task-field}} and');
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
          fields: [{ apiName: 'valid-field', type: EExtraFieldType.Text, name: 'Valid', order: 1 } as unknown as IExtraField],
        },
      });

      const cleaned = cleanTemplateReferences(template);
      const rules = cleaned.tasks[0].conditions[0].rules;
      expect(rules).toHaveLength(1);
      expect(rules[0].field).toBe('valid-field');
    });

    it('falls back to Step N if task name becomes empty', () => {
      const template = createMockTemplate({
        tasks: [
          {
            ...createMockTemplate().tasks[0],
            number: 2,
            name: '{{invalid-field}}',
          },
        ],
      });
      const cleaned = cleanTemplateReferences(template);
      expect(cleaned.tasks[0].name).toBe('Step 2');
    });

    it('safely handles empty rawPerformers array or invalid field performers and preserves valid members', () => {
      const template = createMockTemplate({
        kickoff: {
          ...getEmptyKickoff(),
          fields: [{ apiName: 'valid-user-field', type: EExtraFieldType.User, name: 'Valid User', order: 1 } as unknown as IExtraField],
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
      const cleaned = cleanTemplateReferences(template);
      expect(cleaned.tasks[0].rawPerformers).toHaveLength(2);
      expect(cleaned.tasks[0].rawPerformers.map((p) => p.apiName)).toEqual(['2', '3']);
    });

    it('removes invalid field references from rawDueDate', () => {
      const template = createMockTemplate({
        kickoff: {
          ...getEmptyKickoff(),
          fields: [{ apiName: 'valid-date-field', type: EExtraFieldType.Date, name: 'Valid Date', order: 1 } as unknown as IExtraField],
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
      const cleaned = cleanTemplateReferences(template);
      expect(cleaned.tasks[0].rawDueDate?.sourceId).toBe('valid-date-field');
      expect(cleaned.tasks[0].rawDueDate?.ruleTarget).toBe('field');
      expect(cleaned.tasks[1].rawDueDate?.duration).toBeNull();
      expect(cleaned.tasks[1].rawDueDate?.durationMonths).toBeNull();
      expect(cleaned.tasks[1].rawDueDate?.sourceId).toBeNull();
      expect(cleaned.tasks[1].rawDueDate?.ruleTarget).toBe('task started');
    });
  });
});
});
