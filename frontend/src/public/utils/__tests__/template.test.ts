import {
  ETemplateOwnerType,
  ETemplateOwnerRole,
  ETaskPerformerType,
  ITemplateResponse,
  ITemplate,
} from '../../types/template';
import { ESubscriptionPlan } from '../../types/account';
import { TUserListItem, EUserStatus } from '../../types/user';
import { getNormalizedTemplate, mapTemplateRequest, getEmptyKickoff } from '../template';

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
  });
});
