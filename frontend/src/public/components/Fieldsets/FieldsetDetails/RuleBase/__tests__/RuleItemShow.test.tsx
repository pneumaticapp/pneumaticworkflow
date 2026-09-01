import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { RuleItemShow } from '../RuleItemShow';
import { EExtraFieldType } from '../../../../../types/template';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { IBaseRuleGroupAnd } from '../../../../../types/fieldset';
import { EFieldRuleShowOperator } from '../types';

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

jest.mock('../RuleValueField', () => ({
  FieldsetFieldRulesValue: (props: {
    value?: string;
    onChange: (val: string) => void;
  }) => (
    <input
      data-testid="rule-value-input"
      value={props.value || ''}
      onChange={(e) => props.onChange(e.target.value)}
    />
  ),
}));

describe('RuleItemShow component', () => {
  const mockGroupAndRule: IBaseRuleGroupAnd = {
    apiName: 'and_1',
    field: 'field_1',
    operator: EFieldRuleShowOperator.Equal,
    value: 'test_val',
  };

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

  const mockOperatorOptions = [
    { apiName: EFieldRuleShowOperator.Equal, name: 'Equals' },
    { apiName: EFieldRuleShowOperator.NotEqual, name: 'Not equals' },
  ];

  it('triggers updateRule when field is changed', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemShow
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRuleBaseOperatorOptions={mockOperatorOptions}
        fieldRuleShowFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const selects = screen.getAllByTestId('filter-select');
    fireEvent.change(selects[0], { target: { value: 'field_2' } });

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
      <RuleItemShow
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRuleBaseOperatorOptions={mockOperatorOptions}
        fieldRuleShowFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const selects = screen.getAllByTestId('filter-select');
    fireEvent.change(selects[1], { target: { value: EFieldRuleShowOperator.NotEqual } });

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'or_1',
      groupAndApiName: 'and_1',
      ruleChanges: {
        operator: EFieldRuleShowOperator.NotEqual,
      },
    });
  });

  it('triggers updateRule when value is input', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemShow
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRuleBaseOperatorOptions={mockOperatorOptions}
        fieldRuleShowFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const valueInput = screen.getByTestId('rule-value-input');
    fireEvent.change(valueInput, { target: { value: 'new value' } });

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
      <RuleItemShow
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRuleBaseOperatorOptions={mockOperatorOptions}
        fieldRuleShowFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const selects = screen.getAllByTestId('filter-select');
    fireEvent.change(selects[1], { target: { value: EFieldRuleShowOperator.Exist } });

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'or_1',
      groupAndApiName: 'and_1',
      ruleChanges: {
        operator: EFieldRuleShowOperator.Exist,
        value: '',
      },
    });
  });
});
