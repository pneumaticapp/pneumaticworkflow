import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';
import { RuleItemOperatorValue } from '../RuleItemOperatorValue';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EFieldRuleOperator, EFieldRuleValueType } from '../../../../../types/fieldset';
import { EExtraFieldType } from '../../../../../types/template';
import { EUserGroupType } from '../../../../../types/team';
import { makeFieldRuleValidatorGroupAnd, makeFieldsetRuleGroupAnd } from '../../../../../__stubs__/fieldsets.factory';
import { makeGroup } from '../../../../../__stubs__/team.factory';
import { makeUser } from '../../../../../__stubs__/users.factory';

jest.mock('react-redux', () => ({
  useSelector: jest.fn(),
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
  DropdownList: require('../../../../../__stubs__/uiMocks').DropdownListMock,
  UserSelectOption: (props: { name: string }) => <span>{props.name}</span>,
  FilterSelect: (props: {
    options?: { apiName: string; name?: React.ReactNode; searchByText?: string }[];
    selectedOption?: string;
    onChange: (value: string) => void;
  }) => (
    <select
      data-testid="filter-select"
      value={props.selectedOption || ''}
      onChange={(event) => props.onChange(event.target.value)}
    >
      {props.options?.map((option) => (
        <option key={option.apiName} value={option.apiName}>
          {option.searchByText || (typeof option.name === 'string' ? option.name : '')}
        </option>
      ))}
    </select>
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

const mockState = {
  accounts: {
    users: [makeUser({ id: 1, firstName: 'Alice', lastName: 'Smith' })],
  },
  groups: {
    list: [makeGroup({ id: 1, name: 'Sales Team', type: EUserGroupType.Regular })],
  },
};

describe('RuleItemOperatorValue component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector: (state: typeof mockState) => unknown) =>
      selector(mockState),
    );
  });

  const mockGroupAndRule = makeFieldRuleValidatorGroupAnd({
    apiName: 'and_1',
    operator: EFieldRuleOperator.Equal,
    value: '^[0-9]+$',
  });

  it('triggers updateRule when operator is changed', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemOperatorValue
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldType={EExtraFieldType.Number}
        updateRule={handleUpdateRule}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'operator' });
    userEvent.selectOptions(select, EFieldRuleOperator.NotEqual);

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'or_1',
      groupAndApiName: 'and_1',
      ruleChanges: {
        operator: EFieldRuleOperator.NotEqual,
      },
    });
  });

  it('triggers updateRule when text value is changed', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemOperatorValue
        groupAndRule={{ ...mockGroupAndRule, value: '' }}
        groupOrApiName="or_1"
        fieldType={EExtraFieldType.Number}
        updateRule={handleUpdateRule}
      />,
    );

    const input = screen.getByRole('textbox');
    userEvent.paste(input, '^[a-z]+$');

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'or_1',
      groupAndApiName: 'and_1',
      ruleChanges: {
        value: '^[a-z]+$',
      },
    });
  });

  it('highlights value input error on blur and removes highlight on focus when value is empty', () => {
    const emptyValueRule = makeFieldRuleValidatorGroupAnd({
      apiName: 'and_1',
      operator: EFieldRuleOperator.Equal,
      value: '',
    });

    render(
      <RuleItemOperatorValue
        groupAndRule={emptyValueRule}
        groupOrApiName="or_1"
        fieldType={EExtraFieldType.Number}
        updateRule={jest.fn()}
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

  describe('valueType handling in validators and fieldset sum rules', () => {
    const userValidatorRule = makeFieldRuleValidatorGroupAnd({
      apiName: 'and_1',
      operator: EFieldRuleOperator.Equal,
      value: '1',
      valueType: EFieldRuleValueType.Group,
    });

    it('highlights selected group in User validator value dropdown', () => {
      render(
        <RuleItemOperatorValue
          groupAndRule={userValidatorRule}
          groupOrApiName="or_1"
          fieldType={EExtraFieldType.User}
          updateRule={jest.fn()}
        />,
      );

      const select = screen.getByTestId('filter-select');

      expect(select).toHaveValue('group-1');
    });

    it('saves value and valueType=Group when selecting a group in User validator', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemOperatorValue
          groupAndRule={{ ...userValidatorRule, value: '', valueType: null }}
          groupOrApiName="or_1"
          fieldType={EExtraFieldType.User}
          updateRule={handleUpdateRule}
        />,
      );

      const select = screen.getByTestId('filter-select');
      userEvent.selectOptions(select, 'group-1');

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          value: '1',
          valueType: EFieldRuleValueType.Group,
        },
      });
    });

    it('saves value and valueType=User when selecting a user in User validator', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemOperatorValue
          groupAndRule={{ ...userValidatorRule, value: '', valueType: null }}
          groupOrApiName="or_1"
          fieldType={EExtraFieldType.User}
          updateRule={handleUpdateRule}
        />,
      );

      const select = screen.getByTestId('filter-select');
      userEvent.selectOptions(select, 'user-1');

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          value: '1',
          valueType: EFieldRuleValueType.User,
        },
      });
    });

    it('resets valueType to null when changing User validator operator to Exist', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemOperatorValue
          groupAndRule={userValidatorRule}
          groupOrApiName="or_1"
          fieldType={EExtraFieldType.User}
          updateRule={handleUpdateRule}
        />,
      );

      const operatorSelect = screen.getByRole('combobox', { name: 'operator' });
      userEvent.selectOptions(operatorSelect, EFieldRuleOperator.Exist);

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          operator: EFieldRuleOperator.Exist,
          value: '',
          valueType: null,
        },
      });
    });

    it('omits valueType when switching a non-User validator operator to Exist', () => {
      const handleUpdateRule = jest.fn();
      const numberRuleWithNull = makeFieldRuleValidatorGroupAnd({
        apiName: 'and_1',
        operator: EFieldRuleOperator.Equal,
        value: '10',
        valueType: null,
      });

      render(
        <RuleItemOperatorValue
          groupAndRule={numberRuleWithNull}
          groupOrApiName="or_1"
          fieldType={EExtraFieldType.Number}
          updateRule={handleUpdateRule}
        />,
      );

      const operatorSelect = screen.getByRole('combobox', { name: 'operator' });
      userEvent.selectOptions(operatorSelect, EFieldRuleOperator.Exist);

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          operator: EFieldRuleOperator.Exist,
          value: '',
        },
      });
      expect(handleUpdateRule.mock.calls[0][0].ruleChanges).not.toHaveProperty('valueType');
    });

    it('omits valueType when updating a fieldset sum rule value', () => {
      const handleUpdateRule = jest.fn();
      const fieldsetSumRule = makeFieldsetRuleGroupAnd({
        apiName: 'and_1',
        value: '',
      });

      render(
        <RuleItemOperatorValue
          groupAndRule={fieldsetSumRule}
          groupOrApiName="or_1"
          fieldType={EExtraFieldType.Number}
          isFieldsetRuleset
          updateRule={handleUpdateRule}
        />,
      );

      const input = screen.getByRole('textbox');
      userEvent.paste(input, '250');

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          value: '250',
        },
      });
      expect(handleUpdateRule.mock.calls[0][0].ruleChanges).not.toHaveProperty('valueType');
    });
  });
});
