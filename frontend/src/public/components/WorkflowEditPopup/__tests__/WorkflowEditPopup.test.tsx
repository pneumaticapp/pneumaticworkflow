import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../lang/locales/en_US';

import { WorkflowEditPopup } from '../WorkflowEditPopup';
import { EExtraFieldType } from '../../../types/template';

jest.mock('react-dom', () => {
  const actual = jest.requireActual('react-dom');
  return {
    ...actual,
    default: { ...actual.default, createPortal: (el: React.ReactNode) => el },
  };
});

jest.mock('../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn(() => <div data-testid="extra-field" />),
}));

jest.mock('../../TemplateEdit/InputWithVariables', () => ({
  InputWithVariables: () => <div />,
}));

jest.mock('../../TemplateEdit/TaskForm/utils/getTaskVariables', () => ({
  useWorkflowNameVariables: () => [],
}));

jest.mock('../../UI/DateFormat', () => ({
  DateFormat: () => 'mocked-date',
  DateFormatComponent: () => 'mocked-date',
}));

jest.mock('../../../utils/history', () => ({
  history: { location: { pathname: '/' }, push: jest.fn() },
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

const baseWorkflow = {
  id: 1,
  name: 'Test Workflow',
  description: '',
  wfNameTemplate: null,
  tasksCount: 1,
  performersCount: 1,
  kickoff: {
    description: '',
    fields: [],
  },
};

const baseProps = {
  timezone: 'UTC',
  isAdmin: false,
  isOpen: true,
  isLoading: false,
  accountId: 1,
  closeModal: jest.fn(),
  onRunWorkflow: jest.fn(),
};

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    <IntlProvider locale="en" messages={enMessages}>
      {ui}
    </IntlProvider>,
  );

describe('WorkflowEditPopup', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Filtering fields by isHidden', () => {
    it('renders only visible fields from a mixed list', () => {
      const workflow = {
        ...baseWorkflow,
        kickoff: {
          description: '',
          fields: [
            makeField({ apiName: 'f1', isHidden: true }),
            makeField({ apiName: 'f2', isHidden: false }),
            makeField({ apiName: 'f3' }),
          ],
        },
      };

      renderWithIntl(<WorkflowEditPopup {...baseProps} workflow={workflow} />);

      expect(screen.getAllByTestId('extra-field')).toHaveLength(2);
    });
  });
});
