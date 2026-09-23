import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FieldsetFieldsList } from '../FieldsetFieldsList';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EFieldLabelPosition } from '../../../../../types/fieldset';
import { IExtraField } from '../../../../../types/template';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { ExtraFieldIntl } from '../../../../TemplateEdit/ExtraFields';

function requireJestMock(value: unknown, label: string): jest.Mock {
  if (!jest.isMockFunction(value)) {
    throw new Error(`${label} is not a jest.Mock`);
  }
  return value;
}
jest.mock('react-intl', () => ({
  ...jest.requireActual('react-intl'),
  useIntl: () => intlMock,
}));

jest.mock('../../../../../hooks/useCheckDevice', () => ({
  useCheckDevice: () => ({ isDesktop: true }),
}));

jest.mock('../../../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn((props: {
    field: { apiName: string };
    deleteField: () => void;
    moveFieldUp: () => void;
    moveFieldDown: () => void;
    editField: (props: Partial<IExtraField>) => void;
    onOpenFieldRules?: (ruleset?: unknown) => void;
    isDisabled?: boolean;
    isFieldsetReadOnly?: boolean;
  }) =>
    React.createElement('div', { 'data-testid': `extra-field-${props.field.apiName}` }, [
      React.createElement('button', {
        key: 'del',
        'data-testid': `delete-${props.field.apiName}`,
        onClick: props.deleteField,
      }),
      React.createElement('button', {
        key: 'up',
        'data-testid': `move-up-${props.field.apiName}`,
        onClick: props.moveFieldUp,
      }),
      React.createElement('button', {
        key: 'down',
        'data-testid': `move-down-${props.field.apiName}`,
        onClick: props.moveFieldDown,
      }),
      React.createElement('button', {
        key: 'edit',
        'data-testid': `edit-${props.field.apiName}`,
        onClick: () => props.editField({ name: 'Renamed' }),
      }),
      props.onOpenFieldRules && !props.isDisabled && !props.isFieldsetReadOnly
        && React.createElement('button', {
          key: 'open-rules',
          'data-testid': `open-field-rules-${props.field.apiName}`,
          onClick: () => props.onOpenFieldRules!(),
        }),
    ]),
  ),
}));

jest.mock('../../../../TemplateEdit/ExtraFields/utils/ExtraFieldsMap', () => ({
  ExtraFieldsMap: [{ id: 'string', title: 'Text' }],
}));

jest.mock('../../../../TemplateEdit/ExtraFields/utils/ExtraFieldIcon', () => ({
  ExtraFieldIcon: jest.fn((props: { id: string; onClick: () => void; disabled?: boolean }) =>
    React.createElement('button', {
      'data-testid': `field-icon-${props.id}`,
      disabled: props.disabled,
      onClick: () => {
        if (!props.disabled) {
          props.onClick();
        }
      },
    }),
  ),
}));

describe('FieldsetFieldsList Component', () => {
  const defaultProps = {
    fields: [],
    onFieldsChange: jest.fn(),
    isReadOnly: false,
    labelPosition: EFieldLabelPosition.Top,
    accountId: 1,
    datasetOptions: [],
    rulesets: [],
    onRulesetsChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders "No fields yet" message when fields array is empty', () => {
    render(React.createElement(FieldsetFieldsList, defaultProps));
    expect(screen.getByText(intlMock.formatMessage({ id: 'fieldsets.no-fields' }))).toBeInTheDocument();
  });

  it('renders fields list when fields are present', () => {
    const fields = [makeExtraField({ apiName: 'field_1', order: 1 })];
    render(React.createElement(FieldsetFieldsList, { ...defaultProps, fields }));
    expect(screen.getByTestId('extra-field-field_1')).toBeInTheDocument();
  });

  it('renders readOnly badge when isReadOnly=true', () => {
    render(React.createElement(FieldsetFieldsList, { ...defaultProps, isReadOnly: true }));
    expect(screen.getByText(intlMock.formatMessage({ id: 'fieldsets.readonly-badge' }))).toBeInTheDocument();
  });

  it('triggers onFieldsChange when field icon is clicked', () => {
    const onFieldsChange = jest.fn();
    render(React.createElement(FieldsetFieldsList, { ...defaultProps, onFieldsChange }));
    userEvent.click(screen.getByTestId('field-icon-string'));
    expect(onFieldsChange).toHaveBeenCalledTimes(1);
  });

  it('should trigger both onFieldsChange and onRulesetsChange on field deletion', () => {
    const onFieldsChange = jest.fn();
    const onRulesetsChange = jest.fn();
    const fields = [
      makeExtraField({ apiName: 'f1', order: 2 }),
      makeExtraField({ apiName: 'f2', order: 1 }),
    ];
    render(React.createElement(FieldsetFieldsList, { ...defaultProps, fields, onFieldsChange, onRulesetsChange }));

    userEvent.click(screen.getByTestId('delete-f1'));

    expect(onFieldsChange).toHaveBeenCalledTimes(1);
    expect(onRulesetsChange).toHaveBeenCalledTimes(1);
  });

  it('triggers onFieldsChange on edit, moveUp and moveDown', () => {
    const onFieldsChange = jest.fn();
    const fields = [
      makeExtraField({ apiName: 'f1', order: 2 }),
      makeExtraField({ apiName: 'f2', order: 1 }),
    ];
    render(React.createElement(FieldsetFieldsList, { ...defaultProps, fields, onFieldsChange }));

    userEvent.click(screen.getByTestId('move-down-f1'));
    expect(onFieldsChange).toHaveBeenCalledTimes(1);

    userEvent.click(screen.getByTestId('move-up-f2'));
    expect(onFieldsChange).toHaveBeenCalledTimes(2);

    userEvent.click(screen.getByTestId('edit-f1'));
    expect(onFieldsChange).toHaveBeenCalledTimes(3);
  });

  it('disables field creation icons when isReadOnly=true', () => {
    render(React.createElement(FieldsetFieldsList, { ...defaultProps, isReadOnly: true }));

    const icon = screen.getByTestId('field-icon-string');
    expect(icon).toBeDisabled();
  });

  it('does not disable field creation icons when isReadOnly=false', () => {
    render(React.createElement(FieldsetFieldsList, defaultProps));

    const icon = screen.getByTestId('field-icon-string');
    expect(icon).not.toBeDisabled();
  });

  it('passes isDisabled=true to ExtraFieldIntl when isReadOnly=true', () => {
    const fields = [makeExtraField({ apiName: 'f1', order: 1 })];
    render(React.createElement(FieldsetFieldsList, { ...defaultProps, fields, isReadOnly: true }));

    const mock = requireJestMock(ExtraFieldIntl, 'ExtraFieldIntl');
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    expect(lastCall[0].isDisabled).toBe(true);
  });

  it('passes isDisabled=false to ExtraFieldIntl when isReadOnly=false', () => {
    const fields = [makeExtraField({ apiName: 'f1', order: 1 })];
    render(React.createElement(FieldsetFieldsList, { ...defaultProps, fields }));

    const mock = requireJestMock(ExtraFieldIntl, 'ExtraFieldIntl');
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    expect(lastCall[0].isDisabled).toBe(false);
  });

  describe('open-field-rules integration', () => {
    it('renders open-field-rules button when onOpenFieldRule provided and not readonly', () => {
      const fields = [makeExtraField({ apiName: 'f1', order: 1 })];
      render(React.createElement(FieldsetFieldsList, {
        ...defaultProps,
        fields,
        onOpenFieldRule: jest.fn(),
      }));

      expect(screen.getByTestId('open-field-rules-f1')).toBeInTheDocument();
    });

    it('does not render open-field-rules button when isReadOnly=true', () => {
      const fields = [makeExtraField({ apiName: 'f1', order: 1 })];
      render(React.createElement(FieldsetFieldsList, {
        ...defaultProps,
        fields,
        isReadOnly: true,
        onOpenFieldRule: jest.fn(),
      }));

      expect(screen.queryByTestId('open-field-rules-f1')).not.toBeInTheDocument();
    });

    it('calls onOpenFieldRule with field apiName when button clicked', () => {
      const onOpenFieldRule = jest.fn();
      const fields = [makeExtraField({ apiName: 'f1', order: 1 })];
      render(React.createElement(FieldsetFieldsList, {
        ...defaultProps,
        fields,
        onOpenFieldRule,
      }));

      userEvent.click(screen.getByTestId('open-field-rules-f1'));

      expect(onOpenFieldRule).toHaveBeenCalledTimes(1);
      expect(onOpenFieldRule).toHaveBeenCalledWith('f1', undefined);
    });
  });
});

