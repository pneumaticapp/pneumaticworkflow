import * as React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { TaskCard, ETaskCardViewMode } from '../TaskCard';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../types/template';
import { EFieldLabelPosition } from '../../../types/fieldset';
import { ETaskStatus } from '../../../redux/actions';
import { EWorkflowStatus, EWorkflowsLogSorting } from '../../../types/workflow';
import { IAuthUser, ELoggedState } from '../../../types/redux';
import { EUserStatus } from '../../../types/user';
import { ESubscriptionPlan } from '../../../types/account';
import { MergedOutputList } from '../../MergedOutputList';
import { intlMock } from '../../../__stubs__/intlMock';

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useSelector: jest.fn().mockReturnValue([]),
}));

jest.mock('../../MergedOutputList', () => ({
  MergedOutputList: jest.fn(() => <div data-testid="merged-output-list" />),
}));

jest.mock('../utils/storageOutputs', () => ({
  outputStorage: {
    get: jest.fn(() => undefined),
    save: jest.fn(),
    remove: jest.fn(),
  },
  fieldsetsStorage: {
    get: jest.fn(() => undefined),
    save: jest.fn(),
    remove: jest.fn(),
  },
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
  Button: ({
    label,
    onClick,
    disabled,
  }: {
    label?: React.ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }) => (
    <button type="button" disabled={disabled} onClick={onClick}>
      {label}
    </button>
  ),
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

const baseAuthUser: IAuthUser = {
  id: 1,
  email: 'test@test.com',
  firstName: 'Test',
  lastName: 'User',
  phone: '',
  photo: '',
  type: 'user',
  token: '',
  account: {
    name: '',
    isSubscribed: false,
    billingSync: false,
    tenantName: '',
    billingPlan: ESubscriptionPlan.Free,
    plan: ESubscriptionPlan.Free,
    planExpiration: null,
    leaseLevel: 'standard',
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
  status: EUserStatus.Active,
  loggedState: ELoggedState.LoggedIn,
  invitedUser: { id: '' },
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

    const { fieldsetsStorage, outputStorage } = require('../utils/storageOutputs');
    (fieldsetsStorage.get as jest.Mock).mockImplementation(() => undefined);
    (outputStorage.get as jest.Mock).mockImplementation(() => undefined);
  });

  it('renders MergedOutputList and passes fields and fieldsets', async () => {
    const fieldsets = [
      { id: 1, apiName: 'fs-1', name: 'FS', description: '', fields: [], order: 2, labelPosition: EFieldLabelPosition.Top },
    ];
    const task = {
      ...baseTask,
      output: [makeField({ apiName: 'a', order: 1 })],
      fieldsets,
    };

    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).not.toBeNull();
    });

    const mock = MergedOutputList as jest.Mock;
    expect(mock).toHaveBeenCalled();
    const lastCallProps = mock.mock.calls[mock.mock.calls.length - 1][0];
    expect(lastCallProps).toEqual(
      expect.objectContaining({
        fields: expect.arrayContaining([expect.objectContaining({ apiName: 'a' })]),
        fieldsets,
      }),
    );
  });

  it('passes empty fieldsets when task has no fieldsets', async () => {
    const task = {
      ...baseTask,
      output: [makeField({ apiName: 'a', order: 0 })],
    };

    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).not.toBeNull();
    });

    const mock = MergedOutputList as jest.Mock;
    expect(mock).toHaveBeenCalled();
    const lastCallProps = mock.mock.calls[mock.mock.calls.length - 1][0];
    expect(lastCallProps).toEqual(
      expect.objectContaining({
        fieldsets: [],
      }),
    );
  });

  it('filters out isHidden fields before passing to MergedOutputList', async () => {
    const task = {
      ...baseTask,
      output: [
        makeField({ apiName: 'hidden', isHidden: true }),
        makeField({ apiName: 'visible-1', isHidden: false }),
        makeField({ apiName: 'visible-2' }),
      ],
    };

    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).not.toBeNull();
    });

    const callArgs = (MergedOutputList as jest.Mock).mock.calls[0][0];
    expect(callArgs.fields).toHaveLength(2);
    expect(callArgs.fields.map((field: IExtraField) => field.apiName)).toEqual(
      expect.arrayContaining(['visible-1', 'visible-2']),
    );
  });

  it('saves fieldsets to localStorage when a fieldset field is edited', async () => {
    jest.useFakeTimers();
    const { fieldsetsStorage } = require('../utils/storageOutputs');

    const fieldsets = [
      { id: 1, apiName: 'fs-1', name: 'FS', description: '', fields: [makeField({ apiName: 'f-1' })], order: 0, labelPosition: EFieldLabelPosition.Top },
    ];
    const task = { ...baseTask, output: [], fieldsets };
    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).not.toBeNull();
    });

    const { onEditFieldsetField } = (MergedOutputList as jest.Mock).mock.calls[0][0];
    act(() => {
      onEditFieldsetField('f-1')({ value: 'new value' });
      jest.advanceTimersByTime(300);
    });
    expect(fieldsetsStorage.save).toHaveBeenCalled();

    jest.useRealTimers();
  });

  it('restores fieldset values from localStorage draft and merges them with server data', async () => {
    const { fieldsetsStorage } = require('../utils/storageOutputs');

    const storageFs: IFieldsetData = {
      id: 1,
      apiName: 'fs-1',
      name: 'FS-1',
      description: '',
      order: 1,
      labelPosition: EFieldLabelPosition.Top,
      fields: [makeField({ apiName: 'email', value: 'draft@x.com' })],
    };
    (fieldsetsStorage.get as jest.Mock).mockReturnValue([storageFs]);

    const serverFs1: IFieldsetData = {
      id: 1,
      apiName: 'fs-1',
      name: 'FS-1',
      description: '',
      order: 1,
      labelPosition: EFieldLabelPosition.Top,
      fields: [makeField({ apiName: 'email', value: 'server@x.com' })],
    };
    const serverFs2: IFieldsetData = {
      id: 2,
      apiName: 'fs-2',
      name: 'FS-2',
      description: '',
      order: 2,
      labelPosition: EFieldLabelPosition.Top,
      fields: [makeField({ apiName: 'phone', value: 'server-phone' })],
    };

    const task = { ...baseTask, output: [], fieldsets: [serverFs1, serverFs2] };
    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      const lastCall = (MergedOutputList as jest.Mock).mock.calls[
        (MergedOutputList as jest.Mock).mock.calls.length - 1
      ];
      expect(lastCall[0].fieldsets[0].fields[0].value).toBe('draft@x.com');
    });

    const lastCall = (MergedOutputList as jest.Mock).mock.calls[
      (MergedOutputList as jest.Mock).mock.calls.length - 1
    ];
    const passedFieldsets: IFieldsetData[] = lastCall[0].fieldsets;
    expect(passedFieldsets).toHaveLength(2);
    expect(passedFieldsets[1].fields[0].value).toBe('server-phone');
  });

  it('ignores a foreign fieldset from the draft that does not belong to the current task', async () => {
    const { fieldsetsStorage } = require('../utils/storageOutputs');

    const strangerFs: IFieldsetData = {
      id: 999,
      apiName: 'fs-stranger',
      name: 'Stranger',
      description: '',
      order: 0,
      labelPosition: EFieldLabelPosition.Top,
      fields: [makeField({ apiName: 'wrong', value: 'wrong' })],
    };
    (fieldsetsStorage.get as jest.Mock).mockReturnValue([strangerFs]);

    const serverFs: IFieldsetData = {
      id: 1,
      apiName: 'fs-1',
      name: 'FS-1',
      description: '',
      order: 1,
      labelPosition: EFieldLabelPosition.Top,
      fields: [makeField({ apiName: 'email' })],
    };

    const task = { ...baseTask, output: [], fieldsets: [serverFs] };
    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      expect((MergedOutputList as jest.Mock).mock.calls.length).toBeGreaterThan(0);
    });

    const lastCall = (MergedOutputList as jest.Mock).mock.calls[
      (MergedOutputList as jest.Mock).mock.calls.length - 1
    ];
    const passedFieldsets: IFieldsetData[] = lastCall[0].fieldsets;
    expect(passedFieldsets).toHaveLength(1);
    expect(passedFieldsets[0].apiName).toBe('fs-1');
    expect(
      passedFieldsets.find((fs) => fs.apiName === 'fs-stranger'),
    ).toBeUndefined();
  });

  it('reloads fieldsets from the new task draft when task.id changes', async () => {
    const { fieldsetsStorage } = require('../utils/storageOutputs');

    (fieldsetsStorage.get as jest.Mock).mockImplementation((id: number) => {
      if (id === 100) {
        return [
          {
            id: 1,
            apiName: 'fs',
            name: 'FS',
            description: '',
            order: 0,
            fields: [makeField({ apiName: 'k', value: 'draft-A' })],
          },
        ];
      }
      if (id === 200) {
        return [
          {
            id: 1,
            apiName: 'fs',
            name: 'FS',
            description: '',
            order: 0,
            fields: [makeField({ apiName: 'k', value: 'draft-B' })],
          },
        ];
      }
      return undefined;
    });

    const serverFs = (value: string): IFieldsetData => ({
      id: 1,
      apiName: 'fs',
      name: 'FS',
      description: '',
      order: 0,
      labelPosition: EFieldLabelPosition.Top,
      fields: [makeField({ apiName: 'k', value })],
    });

    const taskA = { ...baseTask, id: 100, output: [], fieldsets: [serverFs('server-A')] };
    const { rerender } = render(<TaskCard {...baseProps} task={taskA} />);

    await waitFor(() => {
      const lastCall = (MergedOutputList as jest.Mock).mock.calls[
        (MergedOutputList as jest.Mock).mock.calls.length - 1
      ];
      expect(lastCall[0].fieldsets[0].fields[0].value).toBe('draft-A');
    });

    const taskB = { ...baseTask, id: 200, output: [], fieldsets: [serverFs('server-B')] };
    rerender(<TaskCard {...baseProps} task={taskB} />);

    await waitFor(() => {
      const lastCall = (MergedOutputList as jest.Mock).mock.calls[
        (MergedOutputList as jest.Mock).mock.calls.length - 1
      ];
      expect(lastCall[0].fieldsets[0].fields[0].value).toBe('draft-B');
    });
  });

  it('on Complete click submits a combined payload: plain outputs + fields of all fieldsets', async () => {
    const setTaskCompleted = jest.fn();
    const fieldsets: IFieldsetData[] = [
      {
        id: 1,
        apiName: 'fs-1',
        name: 'FS-1',
        description: '',
        order: 2,
        labelPosition: EFieldLabelPosition.Top,
        fields: [makeField({ apiName: 'a' }), makeField({ apiName: 'b' })],
      },
      {
        id: 2,
        apiName: 'fs-2',
        name: 'FS-2',
        description: '',
        order: 3,
        labelPosition: EFieldLabelPosition.Top,
        fields: [makeField({ apiName: 'c' })],
      },
    ];
    const task = {
      ...baseTask,
      id: 42,
      output: [makeField({ apiName: 'top' })],
      fieldsets,
    };

    render(<TaskCard {...baseProps} task={task} setTaskCompleted={setTaskCompleted} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).not.toBeNull();
    });

    const completeLabel = intlMock.formatMessage({ id: 'processes.complete-task' });
    userEvent.click(screen.getByRole('button', { name: completeLabel }));

    expect(setTaskCompleted).toHaveBeenCalledTimes(1);
    expect(setTaskCompleted).toHaveBeenCalledWith({
      taskId: 42,
      viewMode: ETaskCardViewMode.Single,
      output: expect.arrayContaining([
        expect.objectContaining({ apiName: 'top' }),
        expect.objectContaining({ apiName: 'a' }),
        expect.objectContaining({ apiName: 'b' }),
        expect.objectContaining({ apiName: 'c' }),
      ]),
    });
    expect(setTaskCompleted.mock.calls[0][0].output).toHaveLength(4);
  });

  it('renders the outputs block when the task has only fieldsets and no plain fields', async () => {
    const fieldsets: IFieldsetData[] = [
      {
        id: 1,
        apiName: 'fs',
        name: 'FS',
        description: '',
        order: 0,
        labelPosition: EFieldLabelPosition.Top,
        fields: [makeField({ apiName: 'k' })],
      },
    ];
    const task = { ...baseTask, output: [], fieldsets };

    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).not.toBeNull();
    });
  });

  it('does not render the outputs block when the task has neither plain fields nor fieldsets', async () => {
    const task = { ...baseTask, output: [], fieldsets: [] };

    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).toBeNull();
    });
  });

  it('does not render the outputs block in Completed status even if fieldsets are present', async () => {
    const task = {
      ...baseTask,
      output: [makeField({ apiName: 'a' })],
      fieldsets: [
        {
          id: 1,
          apiName: 'fs',
          name: 'FS',
          description: '',
          order: 0,
          labelPosition: EFieldLabelPosition.Top,
          fields: [makeField({ apiName: 'k' })],
        },
      ] as IFieldsetData[],
    };

    render(<TaskCard {...baseProps} task={task} status={ETaskStatus.Completed} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).toBeNull();
    });
  });

  it('passes the latest fieldsets with the new value to fieldsetsStorage.save (not stale closure)', async () => {
    jest.useFakeTimers();
    const { fieldsetsStorage } = require('../utils/storageOutputs');

    const fieldsets: IFieldsetData[] = [
      {
        id: 1,
        apiName: 'fs-1',
        name: 'FS-1',
        description: '',
        order: 0,
        labelPosition: EFieldLabelPosition.Top,
        fields: [makeField({ apiName: 'email', value: 'old@x.com' })],
      },
    ];
    const task = { ...baseTask, id: 42, output: [], fieldsets };

    render(<TaskCard {...baseProps} task={task} />);

    await waitFor(() => {
      expect(screen.queryByTestId('merged-output-list')).not.toBeNull();
    });

    const calls = (MergedOutputList as jest.Mock).mock.calls;
    const { onEditFieldsetField } = calls[calls.length - 1][0];

    act(() => {
      onEditFieldsetField('email')({ value: 'new@x.com' });
      jest.advanceTimersByTime(300);
    });

    expect(fieldsetsStorage.save).toHaveBeenCalled();
    const saveCalls = (fieldsetsStorage.save as jest.Mock).mock.calls;
    const lastSaveArgs = saveCalls[saveCalls.length - 1];
    expect(lastSaveArgs[0]).toBe(42);
    const savedFieldsets: IFieldsetData[] = lastSaveArgs[1];
    expect(savedFieldsets).toHaveLength(1);
    expect(savedFieldsets[0].apiName).toBe('fs-1');
    expect(savedFieldsets[0].fields[0].value).toBe('new@x.com');

    jest.useRealTimers();
  });
});
