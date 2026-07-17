import * as React from 'react';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector, useDispatch } from 'react-redux';

import { TemplateEdit } from '../TemplateEdit';
import { cleanTemplateReferences } from '../../../utils/template';
import { getCurrentUser } from '../../../redux/selectors/authUser';
import { getNotDeletedAccountsUsers } from '../../../redux/selectors/accounts';
import { getSubscriptionPlan, getIsUserSubsribed } from '../../../redux/selectors/user';
import { getIsCatalogLoaded } from '../../../redux/selectors/fieldsets';
import { getAITemplate, getTemplateData, getTemplateStatus } from '../../../redux/selectors/template';
import { ETemplateStatus } from '../../../types/redux';

jest.mock('../../../utils/template', () => ({
  cleanTemplateReferences: jest.fn((tpl: any) => tpl),
  getEmptyKickoff: jest.fn(() => ({ description: '', fields: [], fieldsets: [] })),
  getNormalizedTemplateOwners: jest.fn((owners: any) => owners),
  getTemplateIdFromUrl: jest.fn(() => null),
}));

jest.mock('../../../utils/history', () => ({
  checkSomeRouteIsActive: jest.fn(() => false),
  isCreateTemplate: jest.fn(() => false),
}));

jest.mock('../../../utils/users', () => ({
  getNotDeletedUsers: jest.fn((users: unknown[]) => users),
  getUserFullName: jest.fn(() => 'Test User'),
}));

jest.mock('../../../utils/createId', () => ({
  createOwnerApiName: jest.fn(() => 'owner-api'),
  createPerformerApiName: jest.fn(() => 'performer-api'),
  createTaskApiName: jest.fn(() => 'task-api-new'),
  createUUID: jest.fn(() => 'uuid-new'),
}));

jest.mock('../../../utils/dueDate/createEmptyTaskDueDate', () => ({
  createEmptyTaskDueDate: jest.fn(() => ({})),
}));

jest.mock('../../../utils/workflows', () => ({
  moveTask: jest.fn((_from: number, _to: number, tasks: any[]) => tasks),
}));

jest.mock('throttle-debounce', () => ({
  debounce: (_ms: number, fn: (...args: any[]) => any) => fn,
}));

jest.mock('../AutoSaveStatus', () => ({
  AutoSaveStatusContainer: jest.fn(() => null),
}));
jest.mock('../TemplateEntity', () => ({
  TemplateEntity: jest.fn(() => null),
}));
jest.mock('../AddEntityButton', () => ({
  AddEntityButton: jest.fn(
    (props: { entities: { title: string; onAddEntity: (apiName?: string) => void }[] }) =>
      React.createElement(
        'button',
        {
          type: 'button',
          onClick: () => props.entities[0].onAddEntity(),
        },
        'Add',
      ),
  ),
  EEntityTitle: { Task: 'task', Delay: 'delay' },
}));
jest.mock('../Integrations', () => ({
  TemplateIntegrations: jest.fn(() => null),
}));
jest.mock('../KickoffRedux', () => {
  const React = require('react');
  const { useTemplateField } = require('../useTemplateForm');

  return {
    KickoffReduxContainer: jest.fn(() => {
      const { setFieldValue } = useTemplateField();

      return React.createElement(
        'button',
        {
          type: 'button',
          onClick: () => setFieldValue('kickoff', {
            description: 'new',
            fields: [],
            fieldsets: [{ apiName: 'fs-1', fields: [{ apiName: 'fieldset-field' }] }],
          }),
        },
        'Set kickoff',
      );
    }),
  };
});
jest.mock('../TemplateSettings', () => ({
  TemplateSettings: jest.fn(() => null),
}));
jest.mock('../TemplateEditVariablesSync', () => ({
  TemplateEditVariablesSync: jest.fn(() => null),
}));
jest.mock('../ConditionsBanner', () => ({
  ConditionsBanner: jest.fn(() => null),
}));

jest.mock('../TaskForm/Conditions/utils/getKickoffConditions', () => ({
  getKickoffConditions: jest.fn(() => ({ predicates: [] })),
}));
jest.mock('../TaskForm/Conditions/utils/getStartTaskConditions', () => ({
  getStartTaskConditions: jest.fn(() => ({ predicates: [] })),
}));
jest.mock('../TaskForm/Conditions/utils/getEmptyConditions', () => ({
  getEmptyConditions: jest.fn(() => ({ predicates: [] })),
}));

jest.mock('../utils/getClonedTask', () => ({
  getClonedTask: jest.fn((task: any) => task),
}));

jest.mock('../../../redux/selectors/fieldsets', () => ({
  getIsCatalogLoaded: jest.fn(),
}));
jest.mock('../../../redux/selectors/user', () => ({
  getSubscriptionPlan: jest.fn(),
}));

jest.mock('../../UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

const SUBSCRIPTION_PLAN = 'unlimited_month';

describe('TemplateEdit', () => {
  const makeTemplate = (overrides: any = {}) => ({
    id: 1,
    name: 'Tpl',
    description: '',
    isActive: false,
    finalizable: false,
    owners: [],
    tasks: [
      { uuid: 'u-task-1', apiName: 'task-1', number: 1, fields: [], fieldsets: [] } as any,
    ],
    kickoff: { description: '', fields: [], fieldsets: [] },
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: 1,
    performersCount: 0,
    dateUpdated: null,
    updatedBy: null,
    ...overrides,
  });

  const baseProps = () => ({
    match: { params: { id: '1' } },
    location: { pathname: '/templates/edit/1', search: '' },
    authUser: { id: 1, isSuperuser: false } as any,
    template: makeTemplate(),
    aiTemplate: null,
    templateStatus: ETemplateStatus.Saved,
    users: [{ id: 1 }] as any,
    isSubscribed: true,
    loadTemplate: jest.fn(),
    loadTemplateFromSystem: jest.fn(),
    resetTemplateStore: jest.fn(),
    saveTemplate: jest.fn(),
    setTemplate: jest.fn(),
    setTemplateStatus: jest.fn(),
    loadTemplateVariablesSuccess: jest.fn(),
  });

  let currentProps: ReturnType<typeof baseProps>;

  beforeEach(() => {
    jest.clearAllMocks();
    currentProps = baseProps();
    (useDispatch as jest.Mock).mockReturnValue(jest.fn());
    (useSelector as jest.Mock).mockImplementation((selector: unknown) => {
      const props = currentProps;
      if (selector === getCurrentUser) return props.authUser;
      if (selector === getNotDeletedAccountsUsers) return props.users;
      if (selector === getTemplateData) return props.template;
      if (selector === getAITemplate) return props.aiTemplate;
      if (selector === getTemplateStatus) return props.templateStatus;
      if (selector === getIsUserSubsribed) return props.isSubscribed;
      if (selector === getSubscriptionPlan) return SUBSCRIPTION_PLAN;
      if (selector === getIsCatalogLoaded) return true;
      return undefined;
    });
  });

  describe('cleanup of references to fieldset fields', () => {
    it('changing tasks runs cleanTemplateReferences', () => {
      const props = baseProps();
      render(React.createElement(TemplateEdit, props as any));

      userEvent.click(screen.getByRole('button', { name: 'Add' }));

      expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
      const [updatedWorkflow] = (cleanTemplateReferences as jest.Mock).mock.calls[0];
      expect(updatedWorkflow.tasks).toHaveLength(2);
    });

    it('changing kickoff runs cleanTemplateReferences', async () => {
      const props = baseProps();
      render(React.createElement(TemplateEdit, props as any));

      await act(async () => {
        userEvent.click(screen.getByRole('button', { name: 'Set kickoff' }));
      });

      expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
      const [updatedWorkflow] = (cleanTemplateReferences as jest.Mock).mock.calls[0];
      expect(updatedWorkflow.kickoff).toEqual({
        description: 'new',
        fields: [],
        fieldsets: [{ apiName: 'fs-1', fields: [{ apiName: 'fieldset-field' }] }],
      });
    });
  });

  describe('newly added task', () => {
    it('a freshly added task has fieldsets as an empty array, not undefined', () => {
      currentProps = { ...baseProps(), template: makeTemplate({ tasks: [] }) };
      render(React.createElement(TemplateEdit, currentProps as any));

      userEvent.click(screen.getByRole('button', { name: 'Add' }));

      expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
      const newTemplate = (cleanTemplateReferences as jest.Mock).mock.calls[0][0];
      expect(newTemplate.tasks).toHaveLength(1);
      expect(newTemplate.tasks[0].fieldsets).toEqual([]);
    });
  });
});
