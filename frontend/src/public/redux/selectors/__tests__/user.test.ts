import { ELoggedState, IApplicationState, IAuthUser } from '../../../types/redux';
import { ESubscriptionPlan } from '../../../types/account';
import { EUserStatus } from '../../../types/user';
import {
  getCanAccessWorkflows,
  getHasExtendedInterface,
  getHasBasicInterface,
  getIsAdmin,
} from '../user';

const createMockAuthUser = (overrides: Partial<IAuthUser> = {}): IAuthUser => ({
  id: 1,
  email: 'test@example.com',
  token: 'test-token',
  firstName: 'Test',
  lastName: 'User',
  phone: '',
  photo: '',
  type: 'user',
  language: 'en',
  timezone: 'UTC',
  dateFmt: 'MM/DD/YYYY',
  dateFdw: '0',
  status: EUserStatus.Active,
  loading: false,
  invitedUser: { id: '' },
  isAccountOwner: false,
  isDigestSubscriber: false,
  isTasksDigestSubscriber: false,
  isCommentsMentionsSubscriber: false,
  isNewTasksSubscriber: false,
  isNewslettersSubscriber: false,
  isSpecialOffersSubscriber: false,
  loggedState: ELoggedState.LoggedIn,
  isAdmin: false,
  hasWorkflowViewerAccess: false,
  hasWorkflowStarterAccess: false,
  account: {
    name: 'Test Account',
    isSubscribed: true,
    billingSync: false,
    tenantName: '',
    billingPlan: ESubscriptionPlan.Premium,
    plan: ESubscriptionPlan.Premium,
    planExpiration: null,
    leaseLevel: 'standard',
    logoSm: null,
    logoLg: null,
    trialEnded: false,
    trialIsActive: false,
  },
  ...overrides,
});

const createMockState = (authUserOverrides: Partial<IAuthUser> = {}): IApplicationState => ({
  authUser: createMockAuthUser(authUserOverrides),
} as IApplicationState);

describe('user selectors', () => {
  describe('getIsAdmin', () => {
    it('returns true when user is admin', () => {
      const state = createMockState({ isAdmin: true });

      expect(getIsAdmin(state)).toBe(true);
    });

    it('returns false when user is not admin', () => {
      const state = createMockState({ isAdmin: false });

      expect(getIsAdmin(state)).toBe(false);
    });

    it('returns false when isAdmin is undefined', () => {
      const state = createMockState({ isAdmin: undefined });

      expect(getIsAdmin(state)).toBe(false);
    });
  });

  describe('getCanAccessWorkflows', () => {
    it('returns true when user is admin', () => {
      const state = createMockState({
        isAdmin: true,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: false,
      });

      expect(getCanAccessWorkflows(state)).toBe(true);
    });

    it('returns true when user has workflow viewer access', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: true,
        hasWorkflowStarterAccess: false,
      });

      expect(getCanAccessWorkflows(state)).toBe(true);
    });

    it('returns true when user has workflow starter access', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: true,
      });

      expect(getCanAccessWorkflows(state)).toBe(true);
    });

    it('returns true when user has all access flags', () => {
      const state = createMockState({
        isAdmin: true,
        hasWorkflowViewerAccess: true,
        hasWorkflowStarterAccess: true,
      });

      expect(getCanAccessWorkflows(state)).toBe(true);
    });

    it('returns false when user has no access flags', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: false,
      });

      expect(getCanAccessWorkflows(state)).toBe(false);
    });

    it('returns false when access flags are undefined', () => {
      const state = createMockState({
        isAdmin: undefined,
        hasWorkflowViewerAccess: undefined,
        hasWorkflowStarterAccess: undefined,
      });

      expect(getCanAccessWorkflows(state)).toBe(false);
    });
  });

  describe('getHasExtendedInterface', () => {
    it('returns true when user is admin', () => {
      const state = createMockState({
        isAdmin: true,
        hasWorkflowViewerAccess: false,
      });

      expect(getHasExtendedInterface(state)).toBe(true);
    });

    it('returns true when user has workflow viewer access', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: true,
      });

      expect(getHasExtendedInterface(state)).toBe(true);
    });

    it('returns true when user is admin and has viewer access', () => {
      const state = createMockState({
        isAdmin: true,
        hasWorkflowViewerAccess: true,
      });

      expect(getHasExtendedInterface(state)).toBe(true);
    });

    it('returns false when user has only starter access', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: true,
      });

      expect(getHasExtendedInterface(state)).toBe(false);
    });

    it('returns false when user has no special access', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: false,
      });

      expect(getHasExtendedInterface(state)).toBe(false);
    });
  });

  describe('getHasBasicInterface', () => {
    it('returns true when user has only starter access', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: true,
      });

      expect(getHasBasicInterface(state)).toBe(true);
    });

    it('returns false when user is admin with starter access', () => {
      const state = createMockState({
        isAdmin: true,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: true,
      });

      expect(getHasBasicInterface(state)).toBe(false);
    });

    it('returns false when user has viewer and starter access', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: true,
        hasWorkflowStarterAccess: true,
      });

      expect(getHasBasicInterface(state)).toBe(false);
    });

    it('returns false when user has no starter access', () => {
      const state = createMockState({
        isAdmin: false,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: false,
      });

      expect(getHasBasicInterface(state)).toBe(false);
    });

    it('returns false when user is admin without starter access', () => {
      const state = createMockState({
        isAdmin: true,
        hasWorkflowViewerAccess: false,
        hasWorkflowStarterAccess: false,
      });

      expect(getHasBasicInterface(state)).toBe(false);
    });
  });
});
