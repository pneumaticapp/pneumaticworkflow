import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { FieldsetFieldRulesValue } from '../RuleValueField';
import { EExtraFieldType, IExtraFieldSelection } from '../../../../../types/template';
import { EUserStatus } from '../../../../../types/user';
import { intlMock } from '../../../../../__stubs__/intlMock';

const mockState = {
  accounts: {
    users: [
      { id: 1, firstName: 'Alice', lastName: 'Smith', status: EUserStatus.Active, type: 'user' },
      { id: 2, firstName: 'Bob', lastName: 'Jones', status: EUserStatus.Active, type: 'user' },
      { id: 3, firstName: 'Charlie', lastName: 'Brown', status: EUserStatus.Deleted, type: 'user' },
    ],
  },
  authUser: {
    dateFdw: 0,
    language: 'en',
    timezone: 'UTC',
  },
};

jest.mock('react-redux', () => ({
  useSelector: jest.fn((selector) => selector(mockState)),
}));

jest.mock('react-intl', () => {
  const actualIntl = jest.requireActual('react-intl');
  return {
    ...actualIntl,
    useIntl: () => intlMock,
  };
});

jest.mock('../../../../UI', () => ({
  FilterSelect: (props: {
    options?: { apiName: string; name: string }[];
    selectedOption?: string;
    onChange: (val: string) => void;
  }) => (
    <select
      data-testid="filter-select"
      value={props.selectedOption || ''}
      onChange={(e) => props.onChange(e.target.value)}
    >
      {props.options?.map((opt) => (
        <option key={opt.apiName} value={opt.apiName}>
          {opt.name}
        </option>
      ))}
    </select>
  ),
}));

jest.mock('../../../../UI/form/DatePicker', () => ({
  DatePickerCustom: (props: {
    selected?: Date | null;
    onChange: (date: Date | null) => void;
  }) => (
    <input
      data-testid="date-picker"
      value={props.selected ? props.selected.toISOString().substring(0, 10) : ''}
      onChange={(e) => props.onChange(e.target.value ? new Date(e.target.value) : null)}
    />
  ),
}));

jest.mock('react-number-format', () => ({
  NumericFormat: (props: {
    value?: string;
    className?: string;
    onFocus?: () => void;
    onBlur?: () => void;
    onValueChange: (values: { value: string }) => void;
  }) => (
    <input
      data-testid="numeric-format"
      className={props.className}
      value={props.value || ''}
      onFocus={props.onFocus}
      onBlur={props.onBlur}
      onChange={(e) => props.onValueChange({ value: e.target.value })}
    />
  ),
}));

describe('FieldsetFieldRulesValue component', () => {
  it('returns null when fieldType is File', () => {
    const { container } = render(
      <FieldsetFieldRulesValue
        fieldType={EExtraFieldType.File}
        value=""
        onChange={jest.fn()}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('renders user select for User fieldType with active users', () => {
    const handleChange = jest.fn();

    render(
      <FieldsetFieldRulesValue
        fieldType={EExtraFieldType.User}
        value="1"
        onChange={handleChange}
      />,
    );

    const select = screen.getByTestId('filter-select');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('1');

    fireEvent.change(select, { target: { value: '2' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('2');
  });

  it('renders select menu for Radio fieldType using selections', () => {
    const handleChange = jest.fn();
    const selections: IExtraFieldSelection[] = [
      { apiName: '1', value: 'Option A' },
      { apiName: '2', value: 'Option B' },
    ];

    render(
      <FieldsetFieldRulesValue
        fieldType={EExtraFieldType.Radio}
        selections={selections}
        value="Option A"
        onChange={handleChange}
      />,
    );

    const select = screen.getByTestId('filter-select');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('Option A');

    fireEvent.change(select, { target: { value: 'Option B' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('Option B');
  });

  it('renders DatePickerCustom for Date fieldType', () => {
    const handleChange = jest.fn();

    render(
      <FieldsetFieldRulesValue
        fieldType={EExtraFieldType.Date}
        value="1767225600"
        onChange={handleChange}
      />,
    );

    const datePicker = screen.getByTestId('date-picker');
    expect(datePicker).toBeInTheDocument();
    expect(datePicker).toHaveValue('2026-01-01');

    fireEvent.change(datePicker, { target: { value: '2026-12-31' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('renders NumericFormat for Number fieldType', () => {
    const handleChange = jest.fn();

    render(
      <FieldsetFieldRulesValue
        fieldType={EExtraFieldType.Number}
        value="100"
        onChange={handleChange}
      />,
    );

    const numberInput = screen.getByTestId('numeric-format');
    expect(numberInput).toBeInTheDocument();
    expect(numberInput).toHaveValue('100');

    fireEvent.change(numberInput, { target: { value: '250' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('250');
  });

  it('renders default text Input for Text fieldType', () => {
    const handleChange = jest.fn();

    render(
      <FieldsetFieldRulesValue
        fieldType={EExtraFieldType.Text}
        value="Initial Text"
        onChange={handleChange}
      />,
    );

    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('Initial Text');

    fireEvent.change(input, { target: { value: 'Updated Text' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('Updated Text');
  });

  it('highlights error on blur and removes highlight on focus when text value is empty', () => {
    render(
      <FieldsetFieldRulesValue
        fieldType={EExtraFieldType.Text}
        value=""
        onChange={jest.fn()}
      />,
    );

    const input = screen.getByRole('textbox');
    expect(input).not.toHaveClass('rule-value-input_error');

    fireEvent.focus(input);
    fireEvent.blur(input);
    expect(input).toHaveClass('rule-value-input_error');

    fireEvent.focus(input);
    expect(input).not.toHaveClass('rule-value-input_error');
  });
});
