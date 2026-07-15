import * as React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';

import { TaskCard, ETaskCardViewMode } from '../TaskCard';
import { EExtraFieldType, ETemplateOwnerType, IExtraField } from '../../../types/template';
import { ETaskStatus } from '../../../redux/actions';
import { EWorkflowStatus, EWorkflowsLogSorting } from '../../../types/workflow';
import { ExtraFieldIntl } from '../../TemplateEdit/ExtraFields';
import { addOrUpdateStorageOutput } from '../utils/storageOutputs';

jest.mock('../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn(() => <div data-testid="extra-field" />),
}));

const mockExtraFieldIntl = ExtraFieldIntl as unknown as jest.Mock;
const mockButton = jest.fn();

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

jest.mock('react-redux', () => ({
  useSelector: (selector: () => unknown) => selector(),
}));

jest.mock('../../../redux/selectors/groups', () => ({
  getRegularGroupsList: () => [{ id: 5, name: 'Group Five', type: 'regular' }],
}));

const mockUsersDropdown = jest.fn((_props?: unknown) => null);

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

let returnModalOnConfirm: ((comment: string) => void) | undefined;

jest.mock('../ReturnModal', () => ({
  ReturnModal: ({ onConfirm }: { onConfirm: (comment: string) => void }) => {
    returnModalOnConfirm = onConfirm;

    return null;
  },
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
  Button: (props: { disabled?: boolean }) => {
    mockButton(props);

    return <button type="button" disabled={props.disabled} />;
  },
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
    returnModalOnConfirm = undefined;
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

    it('updates visible fields when only server field metadata changes', async () => {
      const field = makeField({ apiName: 'metadata-field', isHidden: false, value: '' });
      const { rerender } = render(
        <TaskCard {...baseProps} task={{ ...baseTask, output: [field] }} />,
      );

      await waitFor(() => {
        expect(screen.getByTestId('extra-field')).toBeInTheDocument();
      });

      rerender(
        <TaskCard {...baseProps} task={{ ...baseTask, output: [{ ...field, isHidden: true }] }} />,
      );

      await waitFor(() => {
        expect(screen.queryByTestId('extra-field')).not.toBeInTheDocument();
      });
    });
  });

  describe('Output uploads', () => {
    it('blocks task completion while a file upload is pending', async () => {
      const task = {
        ...baseTask,
        output: [makeField({ apiName: 'file-field', type: EExtraFieldType.File })],
      };
      render(<TaskCard {...baseProps} task={task} />);

      await waitFor(() => {
        expect(mockExtraFieldIntl).toHaveBeenCalled();
      });
      const fieldProps = mockExtraFieldIntl.mock.calls[0][0];

      act(() => {
        fieldProps.onUploadStateChange(true);
      });

      const completeButtonProps = [...mockButton.mock.calls]
        .reverse()
        .map(([props]) => props)
        .find(({ buttonStyle }) => buttonStyle === 'yellow');

      expect(completeButtonProps.disabled).toBe(true);
      act(() => {
        completeButtonProps.onClick();
      });
      expect(baseProps.setTaskCompleted).not.toHaveBeenCalled();
    });
  });

  describe('Output draft persistence', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('flushes pending output edits before task output updates from the server', async () => {
      const outputField = makeField({ apiName: 'notes', type: EExtraFieldType.Text, value: '' });
      const task = {
        ...baseTask,
        output: [outputField],
      };

      const { rerender } = render(<TaskCard {...baseProps} task={task} />);

      await waitFor(() => {
        expect(mockExtraFieldIntl).toHaveBeenCalled();
      });

      const editField = mockExtraFieldIntl.mock.calls[0][0].editField;

      act(() => {
        editField({ value: 'draft text' });
      });

      expect(addOrUpdateStorageOutput).not.toHaveBeenCalled();

      rerender(
        <TaskCard
          {...baseProps}
          task={{
            ...task,
            output: [{ ...outputField, value: 'server value' }],
          }}
        />,
      );

      expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(1, [
        expect.objectContaining({ apiName: 'notes', value: 'draft text' }),
      ]);
    });

    it('flushes pending output edits on unmount', async () => {
      const outputField = makeField({ apiName: 'notes', type: EExtraFieldType.Text, value: '' });
      const task = {
        ...baseTask,
        output: [outputField],
      };

      const { unmount } = render(<TaskCard {...baseProps} task={task} />);

      await waitFor(() => {
        expect(mockExtraFieldIntl).toHaveBeenCalled();
      });

      const editField = mockExtraFieldIntl.mock.calls[0][0].editField;

      act(() => {
        editField({ value: 'draft text' });
      });

      unmount();

      expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(1, [
        expect.objectContaining({ apiName: 'notes', value: 'draft text' }),
      ]);
    });

    it('flushes pending output edits before requesting task revert', async () => {
      const outputField = makeField({ apiName: 'notes', type: EExtraFieldType.Text, value: '' });
      const task = {
        ...baseTask,
        output: [outputField],
        revertTasks: [{ id: 2, name: 'Previous task', apiName: 'task-2' }],
      };

      const { unmount } = render(<TaskCard {...baseProps} task={task} />);

      await waitFor(() => {
        expect(mockExtraFieldIntl).toHaveBeenCalled();
      });

      const editField = mockExtraFieldIntl.mock.calls[0][0].editField;

      act(() => {
        editField({ value: 'draft text' });
      });

      act(() => {
        returnModalOnConfirm?.('revert comment');
      });

      expect(baseProps.setTaskReverted).toHaveBeenCalledWith({
        taskId: 1,
        viewMode: ETaskCardViewMode.Single,
        comment: 'revert comment',
        clearOutputTaskIds: [1, 2],
      });

      unmount();

      expect(addOrUpdateStorageOutput).toHaveBeenCalledTimes(1);
      expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(1, [
        expect.objectContaining({ apiName: 'notes', value: 'draft text' }),
      ]);
    });
  });
});
