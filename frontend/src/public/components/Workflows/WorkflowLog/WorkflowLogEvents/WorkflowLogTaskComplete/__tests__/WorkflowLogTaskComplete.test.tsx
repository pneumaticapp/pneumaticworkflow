import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../../../../lang/locales/en_US';

import { WorkflowLogTaskComplete } from '../WorkflowLogTaskComplete';
import { KickoffOutputs } from '../../../../../KickoffOutputs';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../../../../types/template';
import { IWorkflowLogTask } from '../../../../../../types/workflow';

jest.mock('../../../../../KickoffOutputs', () => ({
  KickoffOutputs: jest.fn(() => React.createElement('div', { 'data-testid': 'kickoff-outputs' })),
  EKickoffOutputsViewModes: { Short: 'Short', Detailed: 'Detailed' },
}));

jest.mock('../../../../../UserData', () => ({
  UserData: jest.fn(({ children }: { children: (user: Record<string, string> | null) => React.ReactNode }) =>
    children({ id: '1', firstName: 'Test', lastName: 'User', email: 'test@test.com' }),
  ),
}));

jest.mock('../../../../../UI/Avatar', () => ({
  Avatar: () => null,
}));

jest.mock('../../../../../icons', () => ({
  DoneInfoIcon: () => null,
}));

jest.mock('../../../../../UI/DateFormat', () => ({
  DateFormat: () => 'mocked-date',
}));

jest.mock('../../../../../../utils/users', () => ({
  getUserFullName: jest.fn(() => 'Test User'),
}));

jest.mock('../../../../../../utils/helpers', () => {
  const actual = jest.requireActual('../../../../../../utils/helpers');
  return { isArrayWithItems: actual.isArrayWithItems };
});

const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
  apiName: 'f-1',
  name: 'Field',
  type: EExtraFieldType.String,
  value: 'val',
  order: 0,
  userId: null,
  groupId: null,
  ...overrides,
});

const makeFieldset = (overrides: Partial<IFieldsetData> = {}): IFieldsetData => ({
  id: 1,
  apiName: 'fs-1',
  name: 'Fieldset',
  description: '',
  fields: [makeField()],
  order: 0,
  ...overrides,
});

const makeTask = (overrides: Partial<IWorkflowLogTask> = {}): IWorkflowLogTask => ({
  id: 1,
  name: 'Task 1',
  description: '',
  output: [],
  fieldsets: [],
  performers: [],
  dueDate: null,
  number: 1,
  delay: null,
  ...overrides,
});

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    React.createElement(IntlProvider, { locale: 'en', messages: enMessages }, ui),
  );

describe('WorkflowLogTaskComplete', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Fieldsets: render condition and props', () => {
    it('renders KickoffOutputs when output is empty but fieldsets exist', () => {
      const task = makeTask({
        output: [],
        fieldsets: [makeFieldset()],
      });

      renderWithIntl(
        React.createElement(WorkflowLogTaskComplete, {
          userId: 1,
          created: '2024-01-01',
          currentTask: task,
        }),
      );

      expect(screen.getByTestId('kickoff-outputs')).toBeInTheDocument();
      const koMock = KickoffOutputs as unknown as jest.Mock;
      expect(koMock).toHaveBeenCalledTimes(1);
      const lastCallProps = koMock.mock.calls[koMock.mock.calls.length - 1][0];
      expect(lastCallProps.fieldsets).toHaveLength(1);
      expect(lastCallProps.fieldsets[0].apiName).toBe('fs-1');
    });

    it('does not render KickoffOutputs when both output and fieldsets are empty', () => {
      const task = makeTask({
        output: [],
        fieldsets: [],
      });

      renderWithIntl(
        React.createElement(WorkflowLogTaskComplete, {
          userId: 1,
          created: '2024-01-01',
          currentTask: task,
        }),
      );

      expect(screen.queryByTestId('kickoff-outputs')).not.toBeInTheDocument();
    });

    it('passes both outputs and fieldsets from currentTask to KickoffOutputs', () => {
      const outputField = makeField({ apiName: 'out-1', value: 'output-val' });
      const task = makeTask({
        output: [outputField],
        fieldsets: [makeFieldset({ apiName: 'fs-data' })],
      });

      renderWithIntl(
        React.createElement(WorkflowLogTaskComplete, {
          userId: 1,
          created: '2024-01-01',
          currentTask: task,
        }),
      );

      const koMock = KickoffOutputs as unknown as jest.Mock;
      expect(koMock).toHaveBeenCalledTimes(1);
      const lastCallProps = koMock.mock.calls[koMock.mock.calls.length - 1][0];
      expect(lastCallProps.outputs).toEqual(expect.arrayContaining([
        expect.objectContaining({ apiName: 'out-1' }),
      ]));
      expect(lastCallProps.fieldsets).toEqual(expect.arrayContaining([
        expect.objectContaining({ apiName: 'fs-data' }),
      ]));
      expect(lastCallProps.viewMode).toBe('Short');
    });
  });
});
