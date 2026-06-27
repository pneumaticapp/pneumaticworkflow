import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../lang/locales/en_US';

import { EditKickoff } from '../KickoffEdit';
import { makeExtraField } from '../../../__stubs__/fields.factory';
import { makeFieldsetRuntime } from '../../../__stubs__/fieldsets.factory';
import { IExtraField } from '../../../types/template';
import { IFieldsetRuntime } from '../../../types/fieldset';
import { MergedOutputList } from '../../MergedOutputList';

jest.mock('../../MergedOutputList', () => ({
  MergedOutputList: jest.fn(() => <div data-testid="merged-output-list" />),
}));

jest.mock('../../../utils/autoFocusFirstField', () => ({
  autoFocusFirstField: jest.fn(),
}));

jest.mock('../../UI/Loader', () => ({
  Loader: () => null,
}));

jest.mock('../../IntlMessages', () => ({
  IntlMessages: ({ id }: { id: string }) => <span>{id}</span>,
}));

jest.mock('../../UI/Buttons/Button', () => ({
  Button: (props: { label: string; disabled?: boolean; type?: string; onClick?: () => void }) =>
    React.createElement('button', {
      type: props.type || 'button',
      disabled: props.disabled,
      'data-testid': props.type === 'submit' ? 'save-button' : 'cancel-button',
    }, props.label),
}));

const makeField = (apiName: string, order: number, overrides: Partial<IExtraField> = {}) => makeExtraField({
  apiName,
  name: apiName,
  ...(order !== 0 && { order }),
  ...overrides,
});

const makeFieldset = (overrides: Partial<IFieldsetRuntime> & { fields: IExtraField[] }) => makeFieldsetRuntime({
  name: 'Fieldset',
  ...overrides,
});

const baseProps = {
  accountId: 1,
  onEditField: jest.fn(() => jest.fn()),
  onSave: jest.fn(),
};


const renderWithIntl = (ui: React.ReactElement) =>
  render(
    <IntlProvider locale="en" messages={enMessages}>
      {ui}
    </IntlProvider>,
  );

describe('KickoffEdit', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders MergedOutputList and passes fields and fieldsets', () => {
    const kickoff = {
      description: '',
      fields: [makeField('f1', 1)],
      fieldsets: [],
    };
    const fieldsets = [
      makeFieldset({ fields: [], order: 2 }),
    ];

    renderWithIntl(
      <EditKickoff
        {...baseProps}
        kickoff={kickoff}
        fieldsets={fieldsets}
        onEditFieldsetField={jest.fn(() => jest.fn())}
      />,
    );

    expect(screen.queryByTestId('merged-output-list')).not.toBeNull();

    expect(MergedOutputList).toHaveBeenCalledTimes(1);
    expect(MergedOutputList).toHaveBeenCalledWith(
      expect.objectContaining({
        fields: expect.arrayContaining([expect.objectContaining({ apiName: 'f1' })]),
        fieldsets,
      }),
      expect.anything(),
    );
  });

  it('passes empty fieldsets when none provided', () => {
    const kickoff = {
      description: '',
      fields: [makeField('f1', 0), makeField('f2', 1)],
      fieldsets: [],
    };

    renderWithIntl(<EditKickoff {...baseProps} kickoff={kickoff} />);

    expect(screen.queryByTestId('merged-output-list')).not.toBeNull();

    expect(MergedOutputList).toHaveBeenCalledTimes(1);
    expect(MergedOutputList).toHaveBeenCalledWith(
      expect.objectContaining({
        fields: expect.arrayContaining([
          expect.objectContaining({ apiName: 'f1' }),
          expect.objectContaining({ apiName: 'f2' }),
        ]),
        fieldsets: [],
      }),
      expect.anything(),
    );
  });

  it('disables Save button when fieldset contains an empty required field', () => {
    const kickoff = {
      description: '',
      fields: [makeField('f1', 0, { value: 'filled' })],
      fieldsets: [],
    };

    const fieldsets: IFieldsetRuntime[] = [
      makeFieldset({
        fields: [
          makeField('fs-field-1', 1, { isRequired: true, value: '' }),
        ],
        order: 1,
      }),
    ];

    renderWithIntl(
      <EditKickoff
        {...baseProps}
        kickoff={kickoff}
        fieldsets={fieldsets}
        onEditFieldsetField={jest.fn(() => jest.fn())}
      />,
    );

    const saveButton = screen.getByTestId('save-button');
    expect(saveButton).toBeDisabled();
  });

  it('enables Save button when all required fields including fieldsets are filled', () => {
    const kickoff = {
      description: '',
      fields: [makeField('f1', 0, { value: 'filled' })],
      fieldsets: [],
    };

    const fieldsets: IFieldsetRuntime[] = [
      makeFieldset({
        fields: [
          makeField('fs-field-1', 1, { isRequired: true, value: 'also filled' }),
        ],
        order: 1,
      }),
    ];

    renderWithIntl(
      <EditKickoff
        {...baseProps}
        kickoff={kickoff}
        fieldsets={fieldsets}
        onEditFieldsetField={jest.fn(() => jest.fn())}
      />,
    );

    const saveButton = screen.getByTestId('save-button');
    expect(saveButton).not.toBeDisabled();
  });

  it('does not render the form when there are neither plain fields nor fieldsets', () => {
    const kickoff = {
      description: '',
      fields: [],
      fieldsets: [],
    };

    renderWithIntl(<EditKickoff {...baseProps} kickoff={kickoff} fieldsets={[]} />);

    expect(screen.queryByTestId('merged-output-list')).toBeNull();
    expect(screen.queryByTestId('save-button')).toBeNull();
    expect(screen.queryByTestId('cancel-button')).toBeNull();
    expect(MergedOutputList).not.toHaveBeenCalled();
  });

  it('renders the form when there are no plain fields but there are fieldsets', () => {
    const kickoff = {
      description: '',
      fields: [],
      fieldsets: [],
    };

    const fieldsets: IFieldsetRuntime[] = [
      makeFieldset({
        fields: [makeField('fs-field-1', 1)],
        order: 1,
      }),
    ];

    renderWithIntl(
      <EditKickoff
        {...baseProps}
        kickoff={kickoff}
        fieldsets={fieldsets}
        onEditFieldsetField={jest.fn(() => jest.fn())}
      />,
    );

    expect(screen.queryByTestId('merged-output-list')).not.toBeNull();
    expect(MergedOutputList).toHaveBeenCalledTimes(1);
    expect(MergedOutputList).toHaveBeenCalledWith(
      expect.objectContaining({
        fields: [],
        fieldsets,
      }),
      expect.anything(),
    );
  });

  it('forwards onEditField as onEditFieldsetField when a dedicated handler is not provided', () => {
    const onEditField = jest.fn(() => jest.fn());
    const kickoff = {
      description: '',
      fields: [makeField('f1', 0)],
      fieldsets: [],
    };

    const fieldsets: IFieldsetRuntime[] = [
      makeFieldset({
        fields: [makeField('fs-field-1', 1)],
        order: 1,
      }),
    ];

    renderWithIntl(
      <EditKickoff
        accountId={1}
        onSave={jest.fn()}
        onEditField={onEditField}
        kickoff={kickoff}
        fieldsets={fieldsets}
      />,
    );

    expect(MergedOutputList).toHaveBeenCalledTimes(1);
    expect(MergedOutputList).toHaveBeenCalledWith(
      expect.objectContaining({
        onEditField,
        onEditFieldsetField: onEditField,
      }),
      expect.anything(),
    );
  });
});
