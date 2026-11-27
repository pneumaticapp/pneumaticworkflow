import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RuleValueInput } from '../RuleValueInput';
import { EExtraFieldType, IExtraFieldSelection } from '../../../../../types/template';
import { EFieldRuleValueType } from '../../../../../types/fieldset';
import { EUserStatus } from '../../../../../types/user';
import { EUserGroupType } from '../../../../../types/team';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeGroup } from '../../../../../__stubs__/team.factory';

const mockState = {
  accounts: {
    users: [
      { id: 1, firstName: 'Alice', lastName: 'Smith', status: EUserStatus.Active, type: 'user' },
      { id: 2, firstName: 'Bob', lastName: 'Jones', status: EUserStatus.Active, type: 'user' },
      { id: 3, firstName: 'Charlie', lastName: 'Brown', status: EUserStatus.Deleted, type: 'user' },
    ],
  },
  groups: {
    list: [
      makeGroup({ id: 1, name: 'Sales Team', type: EUserGroupType.Regular }),
      makeGroup({ id: 2, name: 'Personal Group', type: EUserGroupType.Personal }),
    ],
  },
  authUser: {
    dateFdw: 0,
    language: 'en',
    timezone: 'UTC',
  },
  datasets: {
    datasetsMap: {
      10: {
        id: 10,
        name: 'Cities',
        items: [
          { id: 101, value: 'New York' },
          { id: 102, value: 'London' },
        ],
      },
    },
  },
};

jest.mock('react-redux', () => ({
  useSelector: jest.fn((selector: (state: typeof mockState) => unknown) => selector(mockState)),
  useDispatch: jest.fn(() => jest.fn()),
}));

jest.mock('react-intl', () => {
  const actualIntl = jest.requireActual('react-intl');
  return {
    ...actualIntl,
    useIntl: () => intlMock,
  };
});

jest.mock('../../../../UI', () => ({
  UserSelectOption: (props: { name: string }) => <span>{props.name}</span>,
  FilterSelect: (props: {
    options?: { apiName: string; name: React.ReactNode; searchByText?: string }[];
    selectedOption?: string;
    isLoading?: boolean;
    isSearchShown?: boolean;
    searchPlaceholder?: string;
    renderPlaceholder?: () => React.ReactNode;
    onChange: (value: string) => void;
  }) => (
    <div>
      <div data-testid="filter-select-placeholder">{props.renderPlaceholder?.()}</div>
      <select
        data-testid="filter-select"
        data-is-loading={props.isLoading ? 'true' : 'false'}
        data-is-search-shown={props.isSearchShown ? 'true' : 'false'}
        data-search-placeholder={props.searchPlaceholder || ''}
        value={props.selectedOption || ''}
        onChange={(event) => props.onChange(event.target.value)}
      >
        {props.options?.map((option) => (
          <option key={option.apiName} value={option.apiName}>
            {option.searchByText || (typeof option.name === 'string' ? option.name : '')}
          </option>
        ))}
      </select>
    </div>
  ),
}));

jest.mock('../../../../UI/form/DatePicker', () => ({
  DatePickerCustom: (props: { selected?: Date | null; onChange: (date: Date | null) => void }) => (
    <input
      data-testid="date-picker"
      value={props.selected ? props.selected.toISOString().substring(0, 10) : ''}
      onChange={(event) => props.onChange(event.target.value ? new Date(event.target.value) : null)}
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
      onChange={(event) => props.onValueChange({ value: event.target.value })}
    />
  ),
}));

describe('RuleValueInput component', () => {
  it('returns null when fieldType is File', () => {
    const { container } = render(<RuleValueInput fieldType={EExtraFieldType.File} value="" onChange={jest.fn()} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('renders user select for User fieldType with active users', () => {
    const handleChange = jest.fn();

    render(<RuleValueInput fieldType={EExtraFieldType.User} value="1" onChange={handleChange} />);

    const select = screen.getByTestId('filter-select');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('user-1');

    userEvent.selectOptions(select, 'user-2');
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('2', EFieldRuleValueType.User);
  });

  it('renders select menu for Radio fieldType using selections', () => {
    const handleChange = jest.fn();
    const selections: IExtraFieldSelection[] = [
      { apiName: '1', value: 'Option A' },
      { apiName: '2', value: 'Option B' },
    ];

    render(
      <RuleValueInput
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

    render(<RuleValueInput fieldType={EExtraFieldType.Date} value="1767225600" onChange={handleChange} />);

    const datePicker = screen.getByTestId('date-picker');
    expect(datePicker).toBeInTheDocument();
    expect(datePicker).toHaveValue('2026-01-01');

    fireEvent.change(datePicker, { target: { value: '2026-12-31' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('renders NumericFormat for Number fieldType', () => {
    const handleChange = jest.fn();

    render(<RuleValueInput fieldType={EExtraFieldType.Number} value="100" onChange={handleChange} />);

    const numberInput = screen.getByTestId('numeric-format');
    expect(numberInput).toBeInTheDocument();
    expect(numberInput).toHaveValue('100');

    fireEvent.change(numberInput, { target: { value: '250' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('250');
  });

  it('renders default text Input for Text fieldType', () => {
    const handleChange = jest.fn();

    render(<RuleValueInput fieldType={EExtraFieldType.Text} value="Initial Text" onChange={handleChange} />);

    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('Initial Text');

    fireEvent.change(input, { target: { value: 'Updated Text' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('Updated Text');
  });

  it('highlights error on blur and removes highlight on focus when text value is empty', () => {
    render(<RuleValueInput fieldType={EExtraFieldType.Text} value="" onChange={jest.fn()} />);

    const input = screen.getByRole('textbox');
    expect(input).not.toHaveClass('rule-value-input_error');

    fireEvent.focus(input);
    fireEvent.blur(input);
    expect(input).toHaveClass('rule-value-input_error');

    fireEvent.focus(input);
    expect(input).not.toHaveClass('rule-value-input_error');
  });

  it('renders select options from dataset when dataset prop is provided', () => {
    const handleChange = jest.fn();

    render(
      <RuleValueInput fieldType={EExtraFieldType.Radio} datasetId={10} value="New York" onChange={handleChange} />,
    );

    const select = screen.getByTestId('filter-select');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('New York');

    fireEvent.change(select, { target: { value: 'London' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('London');
  });

  it('passes isLoading=true prop when loading dataset items', () => {
    render(<RuleValueInput fieldType={EExtraFieldType.Radio} datasetId={999} value="" onChange={jest.fn()} />);

    const select = screen.getByTestId('filter-select');
    expect(select).toHaveAttribute('data-is-loading', 'true');
  });

  it('retains current value in options while dataset is loading', () => {
    render(
      <RuleValueInput fieldType={EExtraFieldType.Radio} datasetId={999} value="Pending City" onChange={jest.fn()} />,
    );

    const select = screen.getByTestId('filter-select');
    expect(select).toHaveValue('Pending City');
  });

  describe('User field delegation and selection placeholders', () => {
    it('forwards valueType=Group to RuleUserValueSelect and displays the selected group', () => {
      render(
        <RuleValueInput
          fieldType={EExtraFieldType.User}
          value="1"
          valueType={EFieldRuleValueType.Group}
          onChange={jest.fn()}
        />,
      );

      const select = screen.getByTestId('filter-select');
      const placeholder = screen.getByTestId('filter-select-placeholder');

      expect(select).toHaveValue('group-1');
      expect(placeholder).toHaveTextContent('Sales Team');
    });

    it('disables search and displays selected text in placeholder for Radio fieldType', () => {
      const selections: IExtraFieldSelection[] = [
        { apiName: '1', value: 'Option A' },
        { apiName: '2', value: 'Option B' },
      ];

      render(
        <RuleValueInput
          fieldType={EExtraFieldType.Radio}
          selections={selections}
          value="Option A"
          onChange={jest.fn()}
        />,
      );

      const select = screen.getByTestId('filter-select');
      const placeholder = screen.getByTestId('filter-select-placeholder');

      expect(select).toHaveAttribute('data-is-search-shown', 'false');
      expect(placeholder).toHaveTextContent('Option A');
    });

    it('displays selected text in placeholder for datasetId options', () => {
      render(<RuleValueInput fieldType={EExtraFieldType.Radio} datasetId={10} value="New York" onChange={jest.fn()} />);

      const placeholder = screen.getByTestId('filter-select-placeholder');

      expect(placeholder).toHaveTextContent('New York');
    });
  });
});
