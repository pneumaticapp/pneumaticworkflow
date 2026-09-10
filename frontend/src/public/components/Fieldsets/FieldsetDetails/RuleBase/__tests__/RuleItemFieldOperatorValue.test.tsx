import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RuleItemFieldOperatorValue } from '../RuleItemFieldOperatorValue';
import { EExtraFieldType } from '../../../../../types/template';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EFieldRuleOperator } from '../../../../../types/fieldset';
import { makeFieldRuleGroupAnd } from '../../../../../__stubs__/fieldsets.factory';

jest.mock('react-intl', () => {
  const actualIntl = jest.requireActual('react-intl');
  return {
    ...actualIntl,
    useIntl: () => intlMock,
  };
});

jest.mock('../../../../UI', () => ({
  DropdownList: require('../../../../../__stubs__/uiMocks').DropdownListMock,
  FilterSelect: (props: {
    options?: { apiName: string; name: string }[];
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
          {option.name}
        </option>
      ))}
    </select>
  ),
}));

jest.mock('../RuleValueInput', () => ({
  RuleValueInput: (props: {
    value?: string;
    onChange: (value: string) => void;
  }) => (
    <input
      data-testid="rule-value-input"
      value={props.value || ''}
      onChange={(event) => props.onChange(event.target.value)}
    />
  ),
}));

describe('RuleItemFieldOperatorValue component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockGroupAndRule = makeFieldRuleGroupAnd({
    apiName: 'and_1',
    field: 'field_1',
    operator: EFieldRuleOperator.Equal,
    value: 'test_val',
  });

  const mockOptions = [
    {
      apiName: 'field_1',
      name: 'Field 1',
      type: EExtraFieldType.Text,
      selections: [],
    },
    {
      apiName: 'field_2',
      name: 'Field 2',
      type: EExtraFieldType.Number,
      selections: [],
    },
  ];

  it('triggers updateRule when field is changed', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemFieldOperatorValue
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRuleShowFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const fieldSelect = screen.getByTestId('filter-select');
    userEvent.selectOptions(fieldSelect, 'field_2');

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'or_1',
      groupAndApiName: 'and_1',
      ruleChanges: {
        field: 'field_2',
        operator: null,
        value: '',
      },
    });
  });

  it('triggers updateRule when operator is changed', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemFieldOperatorValue
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRuleShowFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const operatorSelect = screen.getByRole('combobox', { name: 'operator' });
    userEvent.selectOptions(operatorSelect, EFieldRuleOperator.NotEqual);

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'or_1',
      groupAndApiName: 'and_1',
      ruleChanges: {
        operator: EFieldRuleOperator.NotEqual,
      },
    });
  });

  it('triggers updateRule when value is input', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemFieldOperatorValue
        groupAndRule={{ ...mockGroupAndRule, value: '' }}
        groupOrApiName="or_1"
        fieldRuleShowFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const valueInput = screen.getByTestId('rule-value-input');
    userEvent.paste(valueInput, 'new value');

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'or_1',
      groupAndApiName: 'and_1',
      ruleChanges: {
        value: 'new value',
      },
    });
  });

  it('resets value when operator is changed to one without value', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemFieldOperatorValue
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRuleShowFieldOptions={mockOptions}
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
  });
});
