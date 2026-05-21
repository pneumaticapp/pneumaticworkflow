// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';

import { TemplateEdit } from '../TemplateEdit';
import { cleanTemplateReferences } from '../../../utils/template';
import { KickoffReduxContainer } from '../KickoffRedux';
import { getFieldsetsCatalogByApiName } from '../../../redux/selectors/fieldsets';
import { getSubscriptionPlan } from '../../../redux/selectors/user';
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
jest.mock('../KickoffRedux', () => ({
  KickoffReduxContainer: jest.fn(() => null),
}));
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
  getFieldsetsCatalogByApiName: jest.fn(),
}));
jest.mock('../../../redux/selectors/user', () => ({
  getSubscriptionPlan: jest.fn(),
}));

jest.mock('../../UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

const FIELDSETS_MAP = new Map<string, any>();
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

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector: unknown) => {
      if (selector === getFieldsetsCatalogByApiName) return FIELDSETS_MAP;
      if (selector === getSubscriptionPlan) return SUBSCRIPTION_PLAN;
      return undefined;
    });
  });

  describe('cleanup of references to fieldset fields', () => {
    it('changing tasks runs cleanTemplateReferences with fieldsets catalog and pipes the result into setTemplate', () => {
      const props = baseProps();
      render(React.createElement(TemplateEdit, props as any));

      userEvent.click(screen.getByRole('button', { name: 'Add' }));

      expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
      const [updatedWorkflow, fieldsetsArg] = (cleanTemplateReferences as jest.Mock).mock.calls[0];
      expect(updatedWorkflow.tasks).toHaveLength(2);
      expect(fieldsetsArg).toBe(FIELDSETS_MAP);
      expect(props.setTemplate).toHaveBeenCalledTimes(1);
      expect(props.setTemplate).toHaveBeenCalledWith(updatedWorkflow);
    });

    it('changing kickoff runs cleanTemplateReferences with fieldsets catalog and pipes the result into setTemplate', () => {
      const props = baseProps();
      render(React.createElement(TemplateEdit, props as any));

      const kickoffMock = KickoffReduxContainer as unknown as jest.Mock;
      const lastCall = kickoffMock.mock.calls[kickoffMock.mock.calls.length - 1];
      const setKickoff = lastCall[0].setKickoff as (kickoff: any) => void;

      const newKickoff = {
        description: 'new',
        fields: [],
        fieldsets: [{ apiName: 'fs-1' }],
      };
      setKickoff(newKickoff);

      expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
      const [updatedWorkflow, fieldsetsArg] = (cleanTemplateReferences as jest.Mock).mock.calls[0];
      expect(updatedWorkflow.kickoff).toBe(newKickoff);
      expect(fieldsetsArg).toBe(FIELDSETS_MAP);
      expect(props.setTemplate).toHaveBeenCalledTimes(1);
      expect(props.setTemplate).toHaveBeenCalledWith(updatedWorkflow);
    });
  });

  describe('newly added task', () => {
    it('a freshly added task has fieldsets as an empty array, not undefined', () => {
      const props = { ...baseProps(), template: makeTemplate({ tasks: [] }) };
      render(React.createElement(TemplateEdit, props as any));

      userEvent.click(screen.getByRole('button', { name: 'Add' }));

      expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
      const newTemplate = (cleanTemplateReferences as jest.Mock).mock.calls[0][0];
      expect(newTemplate.tasks).toHaveLength(1);
      expect(newTemplate.tasks[0].fieldsets).toEqual([]);
    });
  });
});
