import { getUserMenuItems } from '../menu';
import { IAuthUser, ELoggedState } from '../../types/redux';
import { EUserStatus } from '../../types/user';
import { ESubscriptionPlan } from '../../types/account';

const createMockUser = (overrides: Partial<IAuthUser> = {}): IAuthUser => ({
  id: 1,
  email: 'test@test.com',
  firstName: 'Test',
  lastName: 'User',
  photo: '',
  phone: '',
  token: 'mock-token',
  type: 'user',
  isAdmin: false,
  isAccountOwner: false,
  isSuperuser: false,
  isSupermode: false,
  status: EUserStatus.Active,
  loading: false,
  invitedUser: { id: '' },
  isDigestSubscriber: false,
  isTasksDigestSubscriber: false,
  isCommentsMentionsSubscriber: false,
  isNewTasksSubscriber: false,
  isNewslettersSubscriber: false,
  isSpecialOffersSubscriber: false,
  loggedState: ELoggedState.LoggedIn,
  language: 'en',
  timezone: 'UTC',
  dateFmt: 'MM/DD/YYYY',
  dateFdw: '0',
  hasWorkflowViewerAccess: false,
  account: {
    id: 1,
    name: 'Test Account',
    logoSm: null,
    logoLg: null,
    leaseLevel: 'standard',
    billingPlan: ESubscriptionPlan.Free,
    plan: ESubscriptionPlan.Free,
    planExpiration: null,
    isVerified: true,
    isSubscribed: false,
    billingSync: true,
    tenantName: 'test',
    trialEnded: false,
    trialIsActive: false,
  },
  ...overrides,
});

describe('getUserMenuItems', () => {
  describe('templates menu item visibility', () => {
    it('should show templates for admin user', () => {
      const user = createMockUser({ isAdmin: true });
      const items = getUserMenuItems(user);
      const templatesItem = items.find((item) => item.id === 'templates');

      expect(templatesItem?.isHidden).toBe(false);
    });

    it('should hide templates for non-admin user without template ownership', () => {
      const user = createMockUser({ isAdmin: false });
      const items = getUserMenuItems(user);
      const templatesItem = items.find((item) => item.id === 'templates');

      expect(templatesItem?.isHidden).toBe(true);
    });

    it('should show templates for non-admin template owner', () => {
      const user = createMockUser({ isAdmin: false });
      const items = getUserMenuItems(user, undefined, { isTemplateOwner: true });
      const templatesItem = items.find((item) => item.id === 'templates');

      expect(templatesItem?.isHidden).toBe(false);
    });

    it('should show templates for admin who is also template owner', () => {
      const user = createMockUser({ isAdmin: true });
      const items = getUserMenuItems(user, undefined, { isTemplateOwner: true });
      const templatesItem = items.find((item) => item.id === 'templates');

      expect(templatesItem?.isHidden).toBe(false);
    });
  });

  describe('other menu items', () => {
    it('should always show dashboard', () => {
      const user = createMockUser({ isAdmin: false });
      const items = getUserMenuItems(user);
      const dashboardItem = items.find((item) => item.id === 'dashboards');

      expect(dashboardItem?.isHidden).toBeUndefined();
    });

    it('should always show tasks', () => {
      const user = createMockUser({ isAdmin: false });
      const items = getUserMenuItems(user);
      const tasksItem = items.find((item) => item.id === 'tasks');

      expect(tasksItem?.isHidden).toBeUndefined();
    });

    it('should hide team for non-admin', () => {
      const user = createMockUser({ isAdmin: false });
      const items = getUserMenuItems(user);
      const teamItem = items.find((item) => item.id === 'team');

      expect(teamItem?.isHidden).toBe(true);
    });

    it('should show team for admin', () => {
      const user = createMockUser({ isAdmin: true });
      const items = getUserMenuItems(user);
      const teamItem = items.find((item) => item.id === 'team');

      expect(teamItem?.isHidden).toBe(false);
    });

    it('should show workflows and highlights if user hasWorkflowStarterAccess', () => {
      const user = createMockUser({ hasWorkflowStarterAccess: true });
      const items = getUserMenuItems(user);
      const workflowsItem = items.find((item) => item.id === 'workflows');
      const highlightsItem = items.find((item) => item.id === 'highlights');

      expect(workflowsItem?.isHidden).toBe(false);
      expect(highlightsItem?.isHidden).toBe(false);
    });

    it('should hide workflows and highlights for normal user', () => {
      const user = createMockUser({ isAdmin: false, hasWorkflowViewerAccess: false, hasWorkflowStarterAccess: false });
      const items = getUserMenuItems(user);
      const workflowsItem = items.find((item) => item.id === 'workflows');
      const highlightsItem = items.find((item) => item.id === 'highlights');

      expect(workflowsItem?.isHidden).toBe(true);
      expect(highlightsItem?.isHidden).toBe(true);
    });
  });
});
