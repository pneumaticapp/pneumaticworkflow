import { checkCanControlWorkflow } from '../checkCanControlWorkflow';
import { IAuthUser, ELoggedState } from '../../../../../types/redux';
import { EUserStatus } from '../../../../../types/user';
import { ESubscriptionPlan } from '../../../../../types/account';

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
  managerId: null,
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

describe('checkCanControlWorkflow', () => {
  describe('account owner', () => {
    it('should return true for account owner regardless of ownership', () => {
      const user = createMockUser({ isAccountOwner: true, isAdmin: false });
      const owners: number[] = [];

      expect(checkCanControlWorkflow(user, owners)).toBe(true);
    });

    it('should return true for account owner even if not in owners list', () => {
      const user = createMockUser({ id: 1, isAccountOwner: true, isAdmin: false });
      const owners = [2, 3, 4];

      expect(checkCanControlWorkflow(user, owners)).toBe(true);
    });
  });

  describe('admin user', () => {
    it('should return true for admin who is workflow owner', () => {
      const user = createMockUser({ id: 1, isAdmin: true, isAccountOwner: false });
      const owners = [1, 2, 3];

      expect(checkCanControlWorkflow(user, owners)).toBe(true);
    });

    it('should return false for admin who is NOT workflow owner', () => {
      const user = createMockUser({ id: 1, isAdmin: true, isAccountOwner: false });
      const owners = [2, 3, 4];

      expect(checkCanControlWorkflow(user, owners)).toBe(false);
    });
  });

  describe('non-admin user', () => {
    it('should return false for non-admin even if workflow owner', () => {
      const user = createMockUser({ id: 1, isAdmin: false, isAccountOwner: false });
      const owners = [1, 2, 3];

      expect(checkCanControlWorkflow(user, owners)).toBe(false);
    });

    it('should return false for non-admin who is not workflow owner', () => {
      const user = createMockUser({ id: 1, isAdmin: false, isAccountOwner: false });
      const owners = [2, 3, 4];

      expect(checkCanControlWorkflow(user, owners)).toBe(false);
    });
  });

  describe('edge cases', () => {
    it('should return false for empty owners list if not account owner', () => {
      const user = createMockUser({ id: 1, isAdmin: true, isAccountOwner: false });
      const owners: number[] = [];

      expect(checkCanControlWorkflow(user, owners)).toBe(false);
    });

    it('should handle single owner correctly', () => {
      const user = createMockUser({ id: 1, isAdmin: true, isAccountOwner: false });
      const owners = [1];

      expect(checkCanControlWorkflow(user, owners)).toBe(true);
    });
  });
});
