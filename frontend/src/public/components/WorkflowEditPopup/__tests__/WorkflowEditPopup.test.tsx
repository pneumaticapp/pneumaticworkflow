// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../lang/locales/en_US';

import { WorkflowEditPopup } from '../WorkflowEditPopup';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../types/template';
import { MergedOutputList } from '../../MergedOutputList';
import { InputWithVariables } from '../../TemplateEdit/InputWithVariables';
import { intlMock } from '../../../__stubs__/intlMock';



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
  InputWithVariables: jest.fn(() => React.createElement('div')),
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

jest.mock('../../UI/Buttons/Button', () => ({
  Button: (props: { label: string; disabled?: boolean; type?: string; onClick?: () => void; isLoading?: boolean }) =>
    React.createElement('button', {
      type: props.type || 'button',
      disabled: props.disabled,
    }, props.label),
}));

jest.mock('../../UI', () => ({
  SectionTitle: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', null, children),
}));

jest.mock('../../RichText', () => ({
  RichText: ({ text }: { text: string }) => React.createElement('span', null, text),
}));

jest.mock('../../icons', () => ({
  PlayLogoIcon: () => null,
}));

const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
  apiName: `f-${Math.random()}`,
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

const formatMsg = (id: string) => intlMock.formatMessage({ id });
const START_LABEL = formatMsg('templates.start-submit');

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
      makeFieldset({ fields: [], order: 2 }),
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

  it('disables Start button when fieldset contains an empty required field', () => {
    const workflow = {
      ...baseWorkflow,
      kickoff: {
        description: '',
        fields: [makeField({ apiName: 'f1', value: 'filled' })],
        fieldsets: [],
      },
      loadedFieldsets: [
        makeFieldset({
          fields: [
            makeField({ apiName: 'fs-field-1', isRequired: true, value: '', order: 1 }),
          ],
          order: 1,
        }),
      ],
    };

    renderWithIntl(<WorkflowEditPopup {...baseProps} workflow={workflow} />);

    const startButton = screen.getByRole('button', { name: START_LABEL });
    expect(startButton).toBeDisabled();
  });

  it('enables Start button when all required fields including fieldsets are filled', () => {
    const workflow = {
      ...baseWorkflow,
      kickoff: {
        description: '',
        fields: [makeField({ apiName: 'f1', value: 'filled' })],
        fieldsets: [],
      },
      loadedFieldsets: [
        makeFieldset({
          fields: [
            makeField({ apiName: 'fs-field-1', isRequired: true, value: 'also filled', order: 1 }),
          ],
          order: 1,
        }),
      ],
    };

    renderWithIntl(<WorkflowEditPopup {...baseProps} workflow={workflow} />);

    const startButton = screen.getByRole('button', { name: START_LABEL });
    expect(startButton).not.toBeDisabled();
  });

  it('passes showInsertButton=false to InputWithVariables', () => {
    renderWithIntl(<WorkflowEditPopup {...baseProps} workflow={baseWorkflow} />);

    expect(InputWithVariables as jest.Mock).toHaveBeenCalledTimes(1);
    expect(InputWithVariables as jest.Mock).toHaveBeenCalledWith(
      expect.objectContaining({ showInsertButton: false }),
      {},
    );
  });
});
