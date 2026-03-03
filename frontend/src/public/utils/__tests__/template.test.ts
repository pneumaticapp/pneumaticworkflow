import {
  ETemplateOwnerType,
  ETemplateViewerType,
  ETemplateStarterType,
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
    },
  ],
  viewers: [],
  starters: [],
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
    },
  ],
  viewers: [],
  starters: [],
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

    it('normalizes template with empty viewers and starters', () => {
      const templateResponse = createMockTemplateResponse({
        viewers: [],
        starters: [],
      });

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.viewers).toEqual([]);
      expect(result.starters).toEqual([]);
    });

    it('normalizes template with viewers', () => {
      const viewers = [
        {
          apiName: 'viewer-123456',
          sourceId: '1',
          type: ETemplateViewerType.User,
        },
        {
          apiName: 'viewer-789012',
          sourceId: '2',
          type: ETemplateViewerType.UserGroup,
        },
      ];
      const templateResponse = createMockTemplateResponse({ viewers });

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.viewers).toEqual(viewers);
    });

    it('normalizes template with starters', () => {
      const starters = [
        {
          apiName: 'starter-123456',
          sourceId: '1',
          type: ETemplateStarterType.User,
        },
        {
          apiName: 'starter-789012',
          sourceId: '3',
          type: ETemplateStarterType.UserGroup,
        },
      ];
      const templateResponse = createMockTemplateResponse({ starters });

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.starters).toEqual(starters);
    });

    it('normalizes template with both viewers and starters', () => {
      const viewers = [
        {
          apiName: 'viewer-123456',
          sourceId: '1',
          type: ETemplateViewerType.User,
        },
      ];
      const starters = [
        {
          apiName: 'starter-123456',
          sourceId: '2',
          type: ETemplateStarterType.User,
        },
      ];
      const templateResponse = createMockTemplateResponse({ viewers, starters });

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.viewers).toEqual(viewers);
      expect(result.starters).toEqual(starters);
    });

    it('handles undefined viewers and starters gracefully', () => {
      const templateResponse = createMockTemplateResponse();
      // @ts-expect-error - testing undefined handling
      delete templateResponse.viewers;
      // @ts-expect-error - testing undefined handling
      delete templateResponse.starters;

      const result = getNormalizedTemplate(
        templateResponse,
        true,
        mockUsers,
        ESubscriptionPlan.Premium,
      );

      expect(result.viewers).toEqual([]);
      expect(result.starters).toEqual([]);
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
    it('maps template with empty viewers and starters', () => {
      const template = createMockTemplate({
        viewers: [],
        starters: [],
      });

      const result = mapTemplateRequest(template);

      expect(result.viewers).toEqual([]);
      expect(result.starters).toEqual([]);
    });

    it('maps template with viewers', () => {
      const viewers = [
        {
          apiName: 'viewer-123456',
          sourceId: '1',
          type: ETemplateViewerType.User,
        },
        {
          apiName: 'viewer-789012',
          sourceId: '2',
          type: ETemplateViewerType.UserGroup,
        },
      ];
      const template = createMockTemplate({ viewers });

      const result = mapTemplateRequest(template);

      expect(result.viewers).toEqual(viewers);
    });

    it('maps template with starters', () => {
      const starters = [
        {
          apiName: 'starter-123456',
          sourceId: '1',
          type: ETemplateStarterType.User,
        },
        {
          apiName: 'starter-789012',
          sourceId: '3',
          type: ETemplateStarterType.UserGroup,
        },
      ];
      const template = createMockTemplate({ starters });

      const result = mapTemplateRequest(template);

      expect(result.starters).toEqual(starters);
    });

    it('maps template with both viewers and starters', () => {
      const viewers = [
        {
          apiName: 'viewer-123456',
          sourceId: '1',
          type: ETemplateViewerType.User,
        },
      ];
      const starters = [
        {
          apiName: 'starter-123456',
          sourceId: '2',
          type: ETemplateStarterType.User,
        },
      ];
      const template = createMockTemplate({ viewers, starters });

      const result = mapTemplateRequest(template);

      expect(result.viewers).toEqual(viewers);
      expect(result.starters).toEqual(starters);
    });

    it('handles undefined viewers and starters with nullish coalescing', () => {
      const template = createMockTemplate();
      // @ts-expect-error - testing undefined handling
      delete template.viewers;
      // @ts-expect-error - testing undefined handling
      delete template.starters;

      const result = mapTemplateRequest(template);

      expect(result.viewers).toEqual([]);
      expect(result.starters).toEqual([]);
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
