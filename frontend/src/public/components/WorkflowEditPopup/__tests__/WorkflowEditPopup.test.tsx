import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../lang/locales/en_US';

import { WorkflowEditPopup } from '../WorkflowEditPopup';
import { EExtraFieldType } from '../../../types/template';
import { MergedOutputList } from '../../MergedOutputList';

jest.mock('react-dom', () => {
  const actual = jest.requireActual('react-dom');
  return {
    ...actual,
    default: { ...actual.default, createPortal: (el: React.ReactNode) => el },
  };
});

jest.mock('../../MergedOutputList', () => ({
  MergedOutputList: jest.fn(() => <div data-testid="merged-output-list" />),
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
    fieldsets: [],
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

  it('renders MergedOutputList and passes fields and fieldsets', () => {
    const loadedFieldsets = [
      { id: 1, apiName: 'fs-1', name: 'FS', description: '', fields: [], order: 2 },
    ];

    const workflow = {
      ...baseWorkflow,
      kickoff: {
        description: '',
        fields: [makeField({ apiName: 'f1', order: 1 })],
        fieldsets: [],
      },
      loadedFieldsets,
    };

    renderWithIntl(<WorkflowEditPopup {...baseProps} workflow={workflow} />);

    expect(screen.queryByTestId('merged-output-list')).not.toBeNull();

    expect(MergedOutputList).toHaveBeenCalledWith(
      expect.objectContaining({
        fields: expect.arrayContaining([expect.objectContaining({ apiName: 'f1' })]),
        fieldsets: loadedFieldsets,
      }),
      expect.anything(),
    );
  });

  it('passes empty fieldsets when workflow has no loadedFieldsets', () => {
    const workflow = {
      ...baseWorkflow,
      kickoff: {
        description: '',
        fields: [makeField({ apiName: 'f1' })],
        fieldsets: [],
      },
    };

    renderWithIntl(<WorkflowEditPopup {...baseProps} workflow={workflow} />);

    expect(screen.queryByTestId('merged-output-list')).not.toBeNull();

    expect(MergedOutputList).toHaveBeenCalledWith(
      expect.objectContaining({
        fieldsets: [],
      }),
      expect.anything(),
    );
  });

  it('filters out isHidden fields before passing to MergedOutputList', () => {
    const workflow = {
      ...baseWorkflow,
      kickoff: {
        description: '',
        fields: [
          makeField({ apiName: 'hidden', isHidden: true }),
          makeField({ apiName: 'visible-1', isHidden: false }),
          makeField({ apiName: 'visible-2' }),
        ],
        fieldsets: [],
      },
    };

    renderWithIntl(<WorkflowEditPopup {...baseProps} workflow={workflow} />);

    const callArgs = (MergedOutputList as jest.Mock).mock.calls[0][0];
    expect(callArgs.fields).toHaveLength(2);
    expect(callArgs.fields.map((f: any) => f.apiName)).toEqual(
      expect.arrayContaining(['visible-1', 'visible-2']),
    );
  });
});
