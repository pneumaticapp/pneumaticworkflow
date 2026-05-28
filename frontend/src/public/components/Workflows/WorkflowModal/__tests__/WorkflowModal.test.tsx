import * as React from 'react';
import { render, act } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../../lang/locales/en_US';

import { WorkflowModal } from '../WorkflowModal';
import { KickoffOutputs } from '../../../KickoffOutputs';
import { EditKickoffContainer } from '../../../KickoffEdit';
import {
  EExtraFieldType,
  IExtraField,
  IFieldsetData,
} from '../../../../types/template';
import {
  EWorkflowStatus,
  EWorkflowsLogSorting,
  IWorkflowDetailsClient,
  IWorkflowDetailsKickoff,
  IWorkflowEdit,
} from '../../../../types/workflow';

jest.mock('react-dom', () => {
  const actual = jest.requireActual('react-dom');
  return {
    ...actual,
    default: { ...actual.default, createPortal: (el: React.ReactNode) => el },
  };
});

jest.mock('reactstrap', () => ({
  Modal: ({ children, isOpen }: { children: React.ReactNode; isOpen: boolean }) =>
    isOpen ? React.createElement('div', { 'data-testid': 'modal' }, children) : null,
  ModalBody: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', null, children),
}));

jest.mock('react-outside-click-handler', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', null, children),
}));

jest.mock('react-textarea-autosize', () => ({
  __esModule: true,
  default: () => React.createElement('textarea'),
}));

jest.mock('../../../KickoffOutputs', () => ({
  KickoffOutputs: jest.fn(() => React.createElement('div', { 'data-testid': 'kickoff-outputs' })),
  EKickoffOutputsViewModes: { Detailed: 'Detailed', Short: 'Short' },
}));

jest.mock('../../../KickoffEdit', () => ({
  EditKickoffContainer: jest.fn(() => React.createElement('div', { 'data-testid': 'edit-kickoff' })),
}));

jest.mock('../../WorkflowLog', () => ({
  WorkflowLog: jest.fn(() => null),
}));

jest.mock('../WorkflowModalHeaderProgressBar', () => ({
  WorkflowModalHeaderProgressBar: jest.fn(() => null),
}));

jest.mock('../../../UserData', () => ({
  UserData: jest.fn(() => null),
}));

jest.mock('../../../UI/Avatar', () => ({
  Avatar: jest.fn(() => null),
}));

jest.mock('../../../UI/Loader', () => ({
  Loader: () => null,
}));

jest.mock('../../../UI/DateFormat', () => ({
  DateFormat: () => 'mocked-date',
}));

jest.mock('../../../UI/TemplateName', () => ({
  TemplateName: () => null,
}));

jest.mock('../../../IntlMessages', () => ({
  IntlMessages: ({ id }: { id: string }) => React.createElement('span', null, id),
}));

jest.mock('../../../icons', () => ({
  EditIcon: () => null,
  ModalCloseIcon: () => React.createElement('button', { 'data-testid': 'close-icon' }),
}));

jest.mock('../../../../utils/workflows', () => ({
  getEditKickoff: jest.fn((kickoff: IWorkflowDetailsKickoff) => ({
    description: kickoff.description || '',
    fields: kickoff.output ? [...kickoff.output] : [],
    fieldsets: [],
  })),
}));

jest.mock('../../../../utils/helpers', () => ({
  getPercent: jest.fn(() => 50),
}));

jest.mock('../../../../utils/users', () => ({
  getUserFullName: jest.fn(() => 'Test User'),
}));

jest.mock('../../../../utils/validators', () => ({
  validateWorkflowName: jest.fn(() => null),
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/getEditedFields', () => ({
  getEditedFields: jest.fn((fields: IExtraField[], apiName: string, changedProps: Partial<IExtraField>) =>
    fields.map((f) => (f.apiName === apiName ? { ...f, ...changedProps } : f)),
  ),
}));

jest.mock('../../utils/getWorkflowProgressColor', () => ({
  getWorkflowProgressColor: jest.fn(() => 'green'),
}));

const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
  apiName: `f-${Math.random().toString(36).slice(2, 6)}`,
  name: 'Field',
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
  ...overrides,
});

const makeFieldset = (overrides: Partial<IFieldsetData> & { fields: IExtraField[] }): IFieldsetData => ({
  id: 1,
  apiName: 'fs-1',
  name: 'Fieldset',
  description: '',
  order: 0,
  ...overrides,
});

const makeWorkflow = (overrides: Partial<IWorkflowDetailsClient> = {}): IWorkflowDetailsClient =>
  ({
    id: 1,
    name: 'Test Workflow',
    owners: [1],
    status: EWorkflowStatus.Running,
    dateCreated: '2024-01-01',
    dateCompleted: null,
    dueDate: null,
    isLegacyTemplate: false,
    legacyTemplateName: '',
    isExternal: false,
    isUrgent: false,
    workflowStarter: 1,
    template: { id: 1, name: 'Template', isActive: true, wfNameTemplate: null },
    description: '',
    kickoff: {
      id: 1,
      description: '',
      output: [],
    },
    finalizable: true,
    tasks: [],
    completedTasks: [],
    areMultipleTasks: false,
    multipleTasksNamesByApiNames: {},
    oneActiveTaskName: null,
    selectedUsers: [],
    tasksCountWithoutSkipped: 0,
    minDelay: null,
    areOverdueTasks: false,
    oldestDeadline: null,
    ...overrides,
  } as IWorkflowDetailsClient);

const makeViewWorkflowEdit = (kickoffOutput: IExtraField[] = []): IWorkflowEdit => ({
  workflow: {
    name: 'Test Workflow',
    kickoff: {
      description: '',
      fields: kickoffOutput,
      fieldsets: [],
    },
  },
  isWorkflowNameEditing: false,
  isWorkflowNameSaving: false,
  isKickoffEditing: false,
  isKickoffSaving: false,
});

const makeEditWorkflowEdit = (kickoffFields: IExtraField[] = []): IWorkflowEdit => ({
  workflow: {
    name: 'Test Workflow',
    kickoff: {
      description: '',
      fields: kickoffFields,
      fieldsets: [],
    },
  },
  isWorkflowNameEditing: false,
  isWorkflowNameSaving: false,
  isKickoffEditing: true,
  isKickoffSaving: false,
});

const baseProps = {
  workflowId: 1,
  isAccountOwner: false,
  sorting: EWorkflowsLogSorting.New,
  isCommentsShown: false,
  isOnlyAttachmentsShown: false,
  isSkippedTasksShown: false,
  isOpen: true,
  timezone: 'UTC',
  dateFmt: 'MM/DD/YYYY',
  items: [],
  isLoading: false,
  isLogLoading: false,
  canEdit: true,
  isRunWorkflowOpen: false,
  isFullscreenImageOpen: false,
  sendWorkflowLogComments: jest.fn(),
  setIsEditWorkflowName: jest.fn(),
  setIsEditKickoff: jest.fn(),
  changeWorkflowLogViewSettings: jest.fn(),
  toggleSkippedTasksVisibility: jest.fn(),
  editWorkflow: jest.fn(),
  setWorkflowEdit: jest.fn(),
  toggleModal: jest.fn(),
};

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    React.createElement(IntlProvider, { locale: 'en', messages: enMessages }, ui),
  );

describe('WorkflowModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Fieldsets: view, edit, merge, cancel', () => {
    it('view mode: KickoffOutputs receives fieldsets from workflow.kickoff.fieldsets', () => {
      const fieldsets: IFieldsetData[] = [
        makeFieldset({ fields: [makeField({ apiName: 'fs-f1', value: 'v1' })], order: 1 }),
      ];

      const workflow = makeWorkflow({
        kickoff: { id: 1, description: '', output: [], fieldsets },
      });

      renderWithIntl(
        React.createElement(WorkflowModal, {
          ...baseProps,
          workflow,
          workflowEdit: makeViewWorkflowEdit(),
        }),
      );

      const koMock = KickoffOutputs as jest.Mock;
      expect(koMock).toHaveBeenCalledTimes(1);
      const lastCallProps = koMock.mock.calls[koMock.mock.calls.length - 1][0];
      expect(lastCallProps.fieldsets).toHaveLength(1);
      expect(lastCallProps.fieldsets).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ apiName: 'fs-1' }),
        ]),
      );
    });

    it('view mode without fieldsets: KickoffOutputs receives fieldsets=[]', () => {
      const workflow = makeWorkflow({
        kickoff: { id: 1, description: '', output: [] },
      });

      renderWithIntl(
        React.createElement(WorkflowModal, {
          ...baseProps,
          workflow,
          workflowEdit: makeViewWorkflowEdit(),
        }),
      );

      const koMock = KickoffOutputs as jest.Mock;
      expect(koMock).toHaveBeenCalledTimes(1);
      const lastCallProps = koMock.mock.calls[koMock.mock.calls.length - 1][0];
      expect(lastCallProps.fieldsets).toEqual([]);
    });

    it('edit mode: EditKickoffContainer receives fieldsets from local state', () => {
      const fsField = makeField({ apiName: 'fs-e1', value: 'edit-val' });
      const fieldsets: IFieldsetData[] = [
        makeFieldset({ fields: [fsField], order: 1 }),
      ];

      const workflow = makeWorkflow({
        kickoff: { id: 1, description: '', output: [], fieldsets },
      });

      renderWithIntl(
        React.createElement(WorkflowModal, {
          ...baseProps,
          workflow,
          workflowEdit: makeEditWorkflowEdit(),
        }),
      );

      const ekMock = EditKickoffContainer as unknown as jest.Mock;
      expect(ekMock).toHaveBeenCalledTimes(1);
      const lastCallProps = ekMock.mock.calls[ekMock.mock.calls.length - 1][0];
      expect(lastCallProps.fieldsets).toHaveLength(1);
      expect(lastCallProps.fieldsets[0].fields).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ apiName: 'fs-e1', value: 'edit-val' }),
        ]),
      );
    });

    it('reinitializes fieldsetFields from new kickoff when workflow changes', () => {
      const fieldsets1: IFieldsetData[] = [
        makeFieldset({ fields: [makeField({ apiName: 'old-field' })], order: 1 }),
      ];
      const fieldsets2: IFieldsetData[] = [
        makeFieldset({
          id: 2,
          apiName: 'fs-new',
          fields: [makeField({ apiName: 'new-field' })],
          order: 1,
        }),
      ];

      const workflow1 = makeWorkflow({
        kickoff: { id: 1, description: '', output: [], fieldsets: fieldsets1 },
      });
      const workflow2 = makeWorkflow({
        kickoff: { id: 2, description: '', output: [], fieldsets: fieldsets2 },
      });

      const editState = makeEditWorkflowEdit();

      const { rerender } = renderWithIntl(
        React.createElement(WorkflowModal, {
          ...baseProps,
          workflow: workflow1,
          workflowEdit: editState,
        }),
      );

      rerender(
        React.createElement(
          IntlProvider,
          { locale: 'en', messages: enMessages },
          React.createElement(WorkflowModal, {
            ...baseProps,
            workflow: workflow2,
            workflowEdit: editState,
          }),
        ),
      );

      const ekMock = EditKickoffContainer as unknown as jest.Mock;
      const lastCallProps = ekMock.mock.calls[ekMock.mock.calls.length - 1][0];
      expect(lastCallProps.fieldsets).toHaveLength(1);
      expect(lastCallProps.fieldsets[0].apiName).toBe('fs-new');
      expect(lastCallProps.fieldsets[0].fields).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ apiName: 'new-field' }),
        ]),
      );
    });

    it('save merges fieldset fields into kickoff.fields and calls editWorkflow', () => {
      const kickoffField = makeField({ apiName: 'k1', value: 'kick-val' });
      const fsField = makeField({ apiName: 'fs-s1', value: 'fs-val' });
      const fieldsets: IFieldsetData[] = [
        makeFieldset({ fields: [fsField], order: 1 }),
      ];

      const workflow = makeWorkflow({
        kickoff: { id: 1, description: '', output: [kickoffField], fieldsets },
      });

      const editState = makeEditWorkflowEdit([kickoffField]);

      renderWithIntl(
        React.createElement(WorkflowModal, {
          ...baseProps,
          workflow,
          workflowEdit: editState,
        }),
      );

      const ekMock = EditKickoffContainer as unknown as jest.Mock;
      const lastCallProps = ekMock.mock.calls[ekMock.mock.calls.length - 1][0];

      act(() => {
        lastCallProps.onSave();
      });

      expect(baseProps.editWorkflow).toHaveBeenCalledTimes(1);
      expect(baseProps.editWorkflow).toHaveBeenCalledWith(
        expect.objectContaining({
          kickoff: expect.objectContaining({
            fields: expect.arrayContaining([
              expect.objectContaining({ apiName: 'k1' }),
              expect.objectContaining({ apiName: 'fs-s1' }),
            ]),
          }),
        }),
      );
    });

    it('cancel calls setIsEditKickoff(false) and resets setWorkflowEdit', () => {
      const fsField = makeField({ apiName: 'fs-c1', value: 'original' });
      const fieldsets: IFieldsetData[] = [
        makeFieldset({ fields: [fsField], order: 1 }),
      ];

      const workflow = makeWorkflow({
        kickoff: { id: 1, description: '', output: [], fieldsets },
      });

      const editState = makeEditWorkflowEdit();

      renderWithIntl(
        React.createElement(WorkflowModal, {
          ...baseProps,
          workflow,
          workflowEdit: editState,
        }),
      );

      baseProps.setWorkflowEdit.mockClear();
      baseProps.setIsEditKickoff.mockClear();

      const ekMock = EditKickoffContainer as unknown as jest.Mock;
      const lastCallProps = ekMock.mock.calls[ekMock.mock.calls.length - 1][0];

      act(() => {
        lastCallProps.onCancel();
      });

      expect(baseProps.setIsEditKickoff).toHaveBeenCalledTimes(1);
      expect(baseProps.setIsEditKickoff).toHaveBeenCalledWith(false);

      expect(baseProps.setWorkflowEdit).toHaveBeenCalledTimes(1);
      expect(baseProps.setWorkflowEdit).toHaveBeenCalledWith(
        expect.objectContaining({
          kickoff: expect.objectContaining({
            description: '',
            fields: [],
          }),
        }),
      );
    });
  });
});
