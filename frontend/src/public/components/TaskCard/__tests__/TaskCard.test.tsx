import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

import { TaskCard, ETaskCardViewMode } from '../TaskCard';
import { EExtraFieldType, IExtraField } from '../../../types/template';
import { ETaskStatus } from '../../../redux/actions';
import { EWorkflowStatus, EWorkflowsLogSorting } from '../../../types/workflow';

jest.mock('../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn(() => <div data-testid="extra-field" />),
}));

jest.mock('../utils/storageOutputs', () => ({
  getOutputFromStorage: jest.fn(() => undefined),
  addOrUpdateStorageOutput: jest.fn(),
}));

jest.mock('../../../utils/autoFocusFirstField', () => ({
  autoFocusFirstField: jest.fn(),
}));

jest.mock('../../../hooks/useCheckDevice', () => ({
  useCheckDevice: () => ({ isMobile: false, isDesktop: true }),
}));

jest.mock('../../UI/form/UsersDropdown', () => ({
  UsersDropdown: () => null,
  EOptionTypes: { User: 'user', Group: 'group' },
}));

jest.mock('../../../utils/history', () => ({
  history: { location: { pathname: '/' } },
}));

jest.mock('../../Workflows/WorkflowLog', () => ({
  WorkflowLog: () => <div />,
}));

jest.mock('../../Workflows/WorkflowLog/WorkflowLogSkeleton', () => ({
  WorkflowLogSkeleton: () => <div />,
}));

jest.mock('../GuestsController', () => ({
  GuestController: React.forwardRef(() => null),
}));

jest.mock('../SubWorkflows', () => ({
  SubWorkflowsContainer: () => <div />,
}));

jest.mock('../../DueIn', () => ({
  DueIn: () => <div />,
}));

jest.mock('../HelpModal/HelpModal', () => ({
  HelpModal: () => null,
}));

jest.mock('../ReturnModal', () => ({
  ReturnModal: () => null,
}));

jest.mock('react-router-dom', () => ({
  Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
}));

jest.mock('../../RichText', () => ({
  RichText: ({ text }: { text: string }) => <span>{text}</span>,
}));

jest.mock('../../../utils/routes', () => ({
  getTaskDetailRoute: jest.fn(() => '/task/1'),
  getWorkflowDetailedRoute: jest.fn(() => '/workflow/1'),
  isTaskDetailRoute: jest.fn(() => false),
}));

jest.mock('../../../utils/analytics', () => ({
  trackInviteTeamInPage: jest.fn(),
}));

jest.mock('../../UI/UserPerformer', () => ({
  UserPerformer: () => <div />,
  EBgColorTypes: {},
}));

jest.mock('../../UI/DateFormat', () => ({
  DateFormat: () => <span />,
}));

jest.mock('../../UserDataWithGroup', () => ({
  __esModule: true,
  default: () => <div />,
}));

jest.mock('../TaskCarkSkeleton', () => ({
  TaskCarkSkeleton: () => <div />,
}));

jest.mock('../checklist', () => ({
  createChecklistExtension: jest.fn(() => []),
  createProgressbarExtension: jest.fn(() => []),
}));

jest.mock('../../UI', () => ({
  Tooltip: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock('../../UI/Typeography/Header', () => ({
  Header: ({ children }: { children: React.ReactNode }) => <h4>{children}</h4>,
}));

jest.mock('../../UI/Buttons/Button', () => ({
  Button: () => <button />,
}));

jest.mock('../../IntlMessages', () => ({
  IntlMessages: ({ id }: { id: string }) => <span>{id}</span>,
}));

jest.mock('../../UI/Loader', () => ({
  Loader: () => null,
}));

jest.mock('../../icons', () => ({
  DoneInfoIcon: () => <svg />,
  InfoIcon: () => <svg />,
  PlayLogoIcon: () => <svg />,
  ReturnTaskInfoIcon: () => <svg />,
  ReturnToIcon: () => <svg />,
}));

const makeField = (overrides = {}) => ({
  apiName: `f-${Math.random()}`,
  name: 'Field',
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
  ...overrides,
});

const baseTask = {
  id: 1,
  name: 'Task 1',
  description: null,
  output: [] as IExtraField[],
  workflow: {
    id: 1,
    name: 'Workflow 1',
    templateName: 'Template 1',
    status: EWorkflowStatus.Running,
    dateCompleted: null,
  },
  performers: [],
  containsComments: false,
  isCompleted: false,
  dateStarted: '2024-01-01',
  dateCompleted: null,
  dueDate: null,
  isUrgent: false,
  subWorkflows: [],
  areChecklistsHandling: false,
  checklistsTotal: 0,
  checklistsMarked: 0,
  checklists: {},
  revertTasks: [],
  helpText: null,
};

const baseWorkflowLog = {
  items: [],
  isCommentsShown: false,
  isOnlyAttachmentsShown: false,
  isSkippedTasksShown: false,
  sorting: EWorkflowsLogSorting.New,
  isOpen: false,
  workflowId: null,
  isLoading: false,
};

const baseAuthUser = {
  id: 1,
  email: 'test@test.com',
  firstName: 'Test',
  lastName: 'User',
  phone: '',
  photo: '',
  type: 'user' as const,
  token: '',
  account: {
    name: '',
    isSubscribed: false,
    billingSync: false,
    tenantName: '',
    billingPlan: 'free' as any,
    plan: 'free' as any,
    planExpiration: null,
    leaseLevel: 'standard' as any,
    logoSm: null,
    logoLg: null,
    trialEnded: false,
    trialIsActive: false,
  },
  isAdmin: false,
  isAccountOwner: false,
  isSuperuser: false,
  loading: false,
  timezone: 'UTC',
  dateFmt: 'MM/dd/yyyy',
  dateFdw: 'Monday',
  language: 'en',
  status: 'active' as any,
  loggedState: 'logged' as any,
  invitedUser: {} as any,
  isDigestSubscriber: false,
  isTasksDigestSubscriber: false,
  isCommentsMentionsSubscriber: false,
  isNewTasksSubscriber: false,
  isNewslettersSubscriber: false,
  isSpecialOffersSubscriber: false,
};

const baseProps = {
  viewMode: ETaskCardViewMode.Single,
  workflowLog: baseWorkflowLog,
  workflow: null,
  status: ETaskStatus.WaitingForAction,
  isWorkflowLoading: false,
  accountId: 1,
  users: [],
  authUser: baseAuthUser,
  addTaskPerformer: jest.fn(),
  removeTaskPerformer: jest.fn(),
  changeTaskWorkflowLog: jest.fn(),
  setTaskCompleted: jest.fn(),
  setTaskReverted: jest.fn(),
  setWorkflowFinished: jest.fn(),
  sendTaskWorkflowLogComments: jest.fn(),
  changeTaskWorkflowLogViewSettings: jest.fn(),
  toggleTaskSkippedTasksVisibility: jest.fn(),
  setCurrentTask: jest.fn(),
  clearWorkflow: jest.fn(),
  openWorkflowLogPopup: jest.fn(),
  setDueDate: jest.fn(),
  deleteDueDate: jest.fn(),
  openSelectTemplateModal: jest.fn(),
};

describe('TaskCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Filtering output fields by isHidden', () => {
    it('renders only visible output fields from a mixed list', async () => {
      const task = {
        ...baseTask,
        output: [
          makeField({ apiName: 'a', isHidden: true }),
          makeField({ apiName: 'b', isHidden: false }),
          makeField({ apiName: 'c' }),
        ],
      };

      render(<TaskCard {...baseProps} task={task} />);

      await waitFor(() => {
        expect(screen.getAllByTestId('extra-field')).toHaveLength(2);
      });
    });
  });
});
