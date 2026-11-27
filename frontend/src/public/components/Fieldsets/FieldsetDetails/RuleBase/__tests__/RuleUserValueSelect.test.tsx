import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';
import { RuleUserValueSelect } from '../RuleUserValueSelect';
import { EFieldRuleValueType } from '../../../../../types/fieldset';
import { EUserStatus } from '../../../../../types/user';
import { EUserGroupType } from '../../../../../types/team';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeGroup } from '../../../../../__stubs__/team.factory';
import { makeUser } from '../../../../../__stubs__/users.factory';

jest.mock('../../../../UI', () => ({
  UserSelectOption: (props: { user?: { type?: string; id?: number }; name: string }) => (
    <span
      data-testid="user-select-option"
      data-avatar-type={props.user?.type ?? ''}
      data-user-id={props.user?.id !== undefined ? String(props.user.id) : ''}
    >
      {props.name}
    </span>
  ),
  FilterSelect: (props: {
    options?: { apiName: string; name: React.ReactNode; searchByText: string }[];
    selectedOption?: string;
    isSearchShown?: boolean;
    isDisabled?: boolean;
    searchPlaceholder?: string;
    renderPlaceholder?: () => React.ReactNode;
    onChange: (value: string) => void;
  }) => (
    <div>
      <div data-testid="filter-select-placeholder">{props.renderPlaceholder?.()}</div>
      <select
        data-is-search-shown={props.isSearchShown ? 'true' : 'false'}
        data-search-placeholder={props.searchPlaceholder || ''}
        disabled={Boolean(props.isDisabled)}
        value={props.selectedOption || ''}
        onChange={(event) => props.onChange(event.target.value)}
      >
        {props.options?.map((option) => (
          <option key={option.apiName} value={option.apiName}>
            {option.searchByText}
          </option>
        ))}
      </select>
      <div data-testid="filter-select-menu">
        {props.options?.map((option) => (
          <div key={option.apiName}>{option.name}</div>
        ))}
      </div>
    </div>
  ),
}));

const mockState = {
  accounts: {
    users: [
      makeUser({ id: 1, firstName: 'Alice', lastName: 'Smith', status: EUserStatus.Active }),
      makeUser({ id: 2, firstName: 'Bob', lastName: 'Jones', status: EUserStatus.Active }),
      makeUser({ id: 3, firstName: 'Charlie', lastName: 'Brown', status: EUserStatus.Deleted }),
    ],
  },
  groups: {
    list: [
      makeGroup({ id: 1, name: 'Sales Team', type: EUserGroupType.Regular }),
      makeGroup({ id: 2, name: 'Personal Group', type: EUserGroupType.Personal }),
    ],
  },
};

const formatMsg = (id: string) => intlMock.formatMessage({ id });
const SEARCH_PLACEHOLDER = formatMsg('nav.search');
const VALUE_PLACEHOLDER = formatMsg('templates.conditions.value-placeholder');

describe('RuleUserValueSelect', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector: (state: typeof mockState) => unknown) =>
      selector(mockState),
    );
  });

  it('lists regular groups first and active users second, excluding personal groups and deleted users', () => {
    render(<RuleUserValueSelect value="" onChange={jest.fn()} />);

    const options = screen.getAllByRole('option');
    const optionEntries = options.map((option) => ({
      value: option.getAttribute('value'),
      text: option.textContent,
    }));

    expect(optionEntries).toEqual([
      { value: 'group-1', text: 'Sales Team' },
      { value: 'user-1', text: 'Alice Smith' },
      { value: 'user-2', text: 'Bob Jones' },
    ]);
  });

  it('renders menu items with UserSelectOption passing group type for groups and user object for users', () => {
    render(<RuleUserValueSelect value="" onChange={jest.fn()} />);

    const items = screen.getAllByTestId('user-select-option');
    const itemsMeta = items.map((item) => ({
      type: item.getAttribute('data-avatar-type'),
      userId: item.getAttribute('data-user-id'),
      text: item.textContent,
    }));

    expect(itemsMeta).toEqual([
      { type: 'group', userId: '', text: 'Sales Team' },
      { type: 'user', userId: '1', text: 'Alice Smith' },
      { type: 'user', userId: '2', text: 'Bob Jones' },
    ]);
  });

  it('passes raw id and valueType=Group when selecting a group colliding with a user id', () => {
    const handleChange = jest.fn();

    render(<RuleUserValueSelect value="" onChange={handleChange} />);

    const select = screen.getByRole('combobox');
    userEvent.selectOptions(select, 'group-1');

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('1', EFieldRuleValueType.Group);
  });

  it('passes raw id and valueType=User when selecting a user', () => {
    const handleChange = jest.fn();

    render(<RuleUserValueSelect value="" onChange={handleChange} />);

    const select = screen.getByRole('combobox');
    userEvent.selectOptions(select, 'user-2');

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('2', EFieldRuleValueType.User);
  });

  it('selects group option and shows group name in placeholder when valueType is Group', () => {
    render(<RuleUserValueSelect value="1" valueType={EFieldRuleValueType.Group} onChange={jest.fn()} />);

    const select = screen.getByRole('combobox');
    const placeholder = screen.getByTestId('filter-select-placeholder');

    expect(select).toHaveValue('group-1');
    expect(placeholder).toHaveTextContent('Sales Team');
  });

  it('selects user option and shows user name in placeholder when valueType is User', () => {
    render(<RuleUserValueSelect value="1" valueType={EFieldRuleValueType.User} onChange={jest.fn()} />);

    const select = screen.getByRole('combobox');
    const placeholder = screen.getByTestId('filter-select-placeholder');

    expect(select).toHaveValue('user-1');
    expect(placeholder).toHaveTextContent('Alice Smith');
  });

  it('falls back to user option for legacy rules with valueType=null', () => {
    render(<RuleUserValueSelect value="1" valueType={null} onChange={jest.fn()} />);

    const select = screen.getByRole('combobox');
    const placeholder = screen.getByTestId('filter-select-placeholder');

    expect(select).toHaveValue('user-1');
    expect(placeholder).toHaveTextContent('Alice Smith');
  });

  it('renders value placeholder when value is empty', () => {
    render(<RuleUserValueSelect value="" valueType={null} onChange={jest.fn()} />);

    const placeholder = screen.getByTestId('filter-select-placeholder');

    expect(placeholder).toHaveTextContent(VALUE_PLACEHOLDER);
  });

  it('enables search with localized nav.search placeholder', () => {
    render(<RuleUserValueSelect value="" onChange={jest.fn()} />);

    const select = screen.getByRole('combobox');

    expect(select).toHaveAttribute('data-is-search-shown', 'true');
    expect(select).toHaveAttribute('data-search-placeholder', SEARCH_PLACEHOLDER);
  });

  it('disables select when isReadOnly is true', () => {
    render(<RuleUserValueSelect value="" isReadOnly onChange={jest.fn()} />);

    expect(screen.getByRole('combobox')).toBeDisabled();
  });

  it('keeps select enabled when isReadOnly is false', () => {
    render(<RuleUserValueSelect value="" isReadOnly={false} onChange={jest.fn()} />);

    expect(screen.getByRole('combobox')).toBeEnabled();
  });

  it('keeps select enabled when isReadOnly is undefined', () => {
    render(<RuleUserValueSelect value="" onChange={jest.fn()} />);

    expect(screen.getByRole('combobox')).toBeEnabled();
  });
});
