import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { RuleItemShow } from '../RuleItemShow';
import { EExtraFieldType } from '../../../../../types/template';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { IBaseRuleGroupAnd } from '../../../../../types/fieldset';

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
    operator: 'equals',
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
    { apiName: 'equals', name: 'Equals' },
    { apiName: 'not_equals', name: 'Not equals' },
  ];

  it('triggers updateRule when field is changed', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemShow
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        ruleOperatorOptions={mockOperatorOptions}
        rulesFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const selects = screen.getAllByTestId('filter-select');
    fireEvent.change(selects[0], { target: { value: 'field_2' } });

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'or_1',
      ruleGroupAndApiName: 'and_1',
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
        ruleOperatorOptions={mockOperatorOptions}
        rulesFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const selects = screen.getAllByTestId('filter-select');
    fireEvent.change(selects[1], { target: { value: 'not_equals' } });

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'or_1',
      ruleGroupAndApiName: 'and_1',
      ruleChanges: {
        operator: 'not_equals',
      },
    });
  });

  it('triggers updateRule when value is input', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemShow
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        ruleOperatorOptions={mockOperatorOptions}
        rulesFieldOptions={mockOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const valueInput = screen.getByTestId('rule-value-input');
    fireEvent.change(valueInput, { target: { value: 'new value' } });

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'or_1',
      ruleGroupAndApiName: 'and_1',
      ruleChanges: {
        value: 'new value',
      },
    });
  });
});
