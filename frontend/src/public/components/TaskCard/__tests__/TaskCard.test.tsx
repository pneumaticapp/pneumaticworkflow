import React, { forwardRef, ReactNode } from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';

import { TaskCard, ETaskCardViewMode } from '../TaskCard';
import { EExtraFieldType, ETemplateOwnerType, IExtraField } from '../../../types/template';
import { ETaskStatus } from '../../../redux/actions';
import { EWorkflowStatus, EWorkflowsLogSorting } from '../../../types/workflow';

jest.mock('../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn(() => <div data-testid="extra-field" />),
}));

jest.mock('../utils/storageOutputs', () => ({
  getOutputFromStorage: jest.fn(() => undefined),
  addOrUpdateStorageOutput: jest.fn(),
  removeOutputFromLocalStorage: jest.fn(),
}));

jest.mock('../../../utils/autoFocusFirstField', () => ({
  autoFocusFirstField: jest.fn(),
}));

jest.mock('../../../hooks/useCheckDevice', () => ({
  useCheckDevice: () => ({ isMobile: false, isDesktop: true }),
}));

jest.mock('react-redux', () => ({
  useSelector: (selector: () => unknown) => selector(),
}));

jest.mock('../../../redux/selectors/groups', () => ({
  getRegularGroupsList: () => [{ id: 5, name: 'Group Five', type: 'regular' }],
}));

const mockUsersDropdown = jest.fn();

jest.mock('../../UI/form/UsersDropdown', () => ({
  UsersDropdown: (props: unknown) => {
    mockUsersDropdown(props);
    return null;
  },
  EOptionTypes: { User: 'user', Group: 'group' },
  getUsersDropdownOptionValue: (optionType: string, id: number | string) => `${optionType}-${id}`,
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
  GuestController: forwardRef(() => null),
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
  Link: ({ children }: { children: ReactNode }) => <a href="/">{children}</a>,
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
  Tooltip: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

jest.mock('../../UI/Typeography/Header', () => ({
  Header: ({ children }: { children: ReactNode }) => <h4>{children}</h4>,
}));

jest.mock('../../UI/Buttons/Button', () => ({
  Button: () => <button type="button" aria-label="Action" />,
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
  managerId: null,
  reportIds: [],
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
    const { getOutputFromStorage } = jest.requireMock('../utils/storageOutputs');
    getOutputFromStorage.mockReturnValue(undefined);
  });

  describe('Performer dropdown', () => {
    it('does not cross-select user and group performers with the same id', async () => {
      const task = {
        ...baseTask,
        performers: [
          { sourceId: 5, type: ETemplateOwnerType.User, label: 'John Doe' },
        ],
      };

      render(
        <TaskCard
          {...baseProps}
          task={task}
          authUser={{ ...baseAuthUser, isAdmin: true }}
          users={[
            {
              id: 5,
              firstName: 'John',
              lastName: 'Doe',
              email: 'john@test.com',
              status: 'active',
            } as any,
          ]}
        />,
      );

      await waitFor(() => {
        expect(mockUsersDropdown).toHaveBeenCalled();
      });

      const lastCall = mockUsersDropdown.mock.calls[mockUsersDropdown.mock.calls.length - 1];
      const dropdownProps = lastCall?.[0] as {
        value: Array<{ optionType: string; id: number }>;
        options: Array<{ optionType: string; id: number; value: string }>;
      };

      expect(dropdownProps.value).toHaveLength(1);
      expect(dropdownProps.value[0]).toMatchObject({ optionType: 'user', id: 5 });

      const userOption = dropdownProps.options.find((option) => option.optionType === 'user' && option.id === 5);
      const groupOption = dropdownProps.options.find((option) => option.optionType === 'group' && option.id === 5);

      expect(userOption?.value).toBe('user-5');
      expect(groupOption?.value).toBe('group-5');
    });
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

  describe('Output field ordering', () => {
    it('renders output fields sorted by order descending to match the template', async () => {
      const { ExtraFieldIntl } = jest.requireMock('../../TemplateEdit/ExtraFields');

      const task = {
        ...baseTask,
        output: [
          makeField({ apiName: 'url-field', name: 'Presentation URL', type: EExtraFieldType.Url, order: 0 }),
          makeField({ apiName: 'file-field', name: 'Presentation file', type: EExtraFieldType.File, order: 1 }),
        ],
      };

      render(<TaskCard {...baseProps} task={task} />);

      await waitFor(() => {
        expect(ExtraFieldIntl).toHaveBeenCalled();
      });

      const renderedApiNames = ExtraFieldIntl.mock.calls.map((call: any[]) => call[0].field.apiName);

      expect(renderedApiNames).toEqual(['file-field', 'url-field']);
    });
  });

  describe('Output synchronization', () => {
    it('cancels a pending storage write when server output changes', () => {
      jest.useFakeTimers();

      try {
        const { ExtraFieldIntl } = jest.requireMock('../../TemplateEdit/ExtraFields');
        const { addOrUpdateStorageOutput } = jest.requireMock('../utils/storageOutputs');
        const field = makeField({ apiName: 'url-field', value: 'https://server.example' });
        const { rerender } = render(
          <TaskCard {...baseProps} task={{ ...baseTask, output: [field] }} />,
        );
        const lastCall = ExtraFieldIntl.mock.calls[ExtraFieldIntl.mock.calls.length - 1];

        act(() => {
          lastCall[0].editField({ value: 'https://draft.example' });
        });

        rerender(
          <TaskCard
            {...baseProps}
            task={{
              ...baseTask,
              output: [{ ...field, value: 'https://updated-server.example' }],
            }}
          />,
        );

        act(() => {
          jest.advanceTimersByTime(300);
        });

        expect(addOrUpdateStorageOutput).not.toHaveBeenCalled();
      } finally {
        jest.useRealTimers();
      }
    });

    it('discards a stale draft when server output is cleared', async () => {
      const { ExtraFieldIntl } = jest.requireMock('../../TemplateEdit/ExtraFields');
      const { addOrUpdateStorageOutput, getOutputFromStorage } = jest.requireMock('../utils/storageOutputs');
      const field = makeField({ apiName: 'url-field', value: 'https://server.example' });
      getOutputFromStorage.mockReturnValue([{ ...field, value: 'https://draft.example' }]);
      const { rerender } = render(
        <TaskCard {...baseProps} task={{ ...baseTask, output: [field] }} />,
      );

      rerender(
        <TaskCard
          {...baseProps}
          task={{ ...baseTask, output: [{ ...field, value: '' }] }}
        />,
      );

      await waitFor(() => {
        const lastCall = ExtraFieldIntl.mock.calls[ExtraFieldIntl.mock.calls.length - 1];
        expect(lastCall[0].field.value).toBe('');
      });
      expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(baseTask.id, []);
    });

    it('preserves drafts for unchanged empty fields when another server field changes', async () => {
      const { ExtraFieldIntl } = jest.requireMock('../../TemplateEdit/ExtraFields');
      const { addOrUpdateStorageOutput, getOutputFromStorage } = jest.requireMock('../utils/storageOutputs');
      const emptyField = makeField({ apiName: 'empty-field', order: 1, value: '' });
      const changedField = makeField({ apiName: 'changed-field', order: 0, value: 'server value' });
      const emptyFieldDraft = { ...emptyField, value: 'local draft' };
      const changedFieldDraft = { ...changedField, value: 'stale local draft' };
      getOutputFromStorage.mockReturnValue([emptyFieldDraft, changedFieldDraft]);
      const { rerender } = render(
        <TaskCard {...baseProps} task={{ ...baseTask, output: [emptyField, changedField] }} />,
      );

      rerender(
        <TaskCard
          {...baseProps}
          task={{
            ...baseTask,
            output: [emptyField, { ...changedField, value: 'updated server value' }],
          }}
        />,
      );

      await waitFor(() => {
        const renderedFields = ExtraFieldIntl.mock.calls
          .slice(-2)
          .map((call: Array<{ field: IExtraField }>) => call[0].field);
        expect(renderedFields).toEqual([
          expect.objectContaining({ apiName: 'empty-field', value: 'local draft' }),
          expect.objectContaining({ apiName: 'changed-field', value: 'updated server value' }),
        ]);
      });
      expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(baseTask.id, [emptyFieldDraft]);
    });
  });
});
