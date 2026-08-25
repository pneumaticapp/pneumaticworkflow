import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

import { RuleItem } from '../RuleItem';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeFieldsetRuleGroupAnd } from '../../../../../__stubs__/fieldsets.factory';
import { EFieldsetNumberRulesetOperator, ERuleCombinator } from '../../../../../types/fieldset';

jest.mock('../../../../UI', () => ({
  FilterSelect: (props: any) => (
    <select
      data-testid="filter-select"
      value={props.selectedOption}
      disabled={props.isDisabled}
      onChange={(e) => props.onChange(e.target.value)}
    >
      {props.options?.map((opt: any) => (
        <option key={opt.apiName} value={opt.apiName}>
          {opt.name}
        </option>
      ))}
    </select>
  ),
  SelectMenu: (props: any) => (
    <select
      data-testid="select-menu"
      value={props.activeValue}
      disabled={props.isDisabled}
      onChange={(e) => props.onChange(e.target.value)}
    >
      {props.values?.map((v: any) => (
        <option key={v} value={v}>
          {v}
        </option>
      ))}
    </select>
  ),
}));

describe('RuleItem component', () => {
  const mockUpdateRule = jest.fn();
  const mockDeleteRule = jest.fn();
  const mockRegroupRules = jest.fn();

  const defaultOperatorOptions = [
    { apiName: EFieldsetNumberRulesetOperator.SumEqual, name: 'Sum is equal to' },
    { apiName: EFieldsetNumberRulesetOperator.SumGreaterThan, name: 'Sum is greater than' },
  ];

  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders rule values and operator selector correctly', () => {
    const groupAndRule = makeFieldsetRuleGroupAnd({
      apiName: 'g-and-1',
      operator: EFieldsetNumberRulesetOperator.SumEqual,
      value: '100',
    });

    render(
      <RuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="g-or-1"
        groupOrIndex={0}
        groupAndIndex={0}
        ruleOperatorOptions={defaultOperatorOptions}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    expect(screen.getByDisplayValue('100')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: formatMsg('fieldsets.rule-delete') }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId('select-menu')).not.toBeInTheDocument();
  });

  it('renders combinator select for non-first rules and triggers regroupRules on change', () => {
    const groupAndRule = makeFieldsetRuleGroupAnd({
      apiName: 'g-and-2',
      operator: EFieldsetNumberRulesetOperator.SumEqual,
      value: '200',
    });

    render(
      <RuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="g-or-1"
        groupOrIndex={0}
        groupAndIndex={1}
        ruleOperatorOptions={defaultOperatorOptions}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const combinatorSelect = screen.getByTestId('select-menu');
    expect(combinatorSelect).toBeInTheDocument();

    fireEvent.change(combinatorSelect, { target: { value: ERuleCombinator.Or } });

    expect(mockRegroupRules).toHaveBeenCalledWith({
      groupOrApiName: 'g-or-1',
      groupAndApiName: 'g-and-2',
      ruleCombinator: ERuleCombinator.Or,
    });
  });

  it('triggers updateRule on value change', () => {
    const groupAndRule = makeFieldsetRuleGroupAnd({
      apiName: 'g-and-1',
      operator: EFieldsetNumberRulesetOperator.SumEqual,
      value: '100',
    });

    render(
      <RuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="g-or-1"
        groupOrIndex={0}
        groupAndIndex={0}
        ruleOperatorOptions={defaultOperatorOptions}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const input = screen.getByDisplayValue('100');
    fireEvent.change(input, { target: { value: '150' } });

    expect(mockUpdateRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'g-or-1',
      ruleGroupAndApiName: 'g-and-1',
      ruleChanges: { value: '150' },
    });
  });

  it('triggers deleteRule on delete button click', () => {
    const groupAndRule = makeFieldsetRuleGroupAnd({
      apiName: 'g-and-1',
      operator: EFieldsetNumberRulesetOperator.SumEqual,
      value: '100',
    });

    render(
      <RuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="g-or-1"
        groupOrIndex={0}
        groupAndIndex={0}
        ruleOperatorOptions={defaultOperatorOptions}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const deleteBtn = screen.getByRole('button', { name: formatMsg('fieldsets.rule-delete') });
    fireEvent.click(deleteBtn);

    expect(mockDeleteRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'g-or-1',
      ruleGroupAndApiName: 'g-and-1',
    });
  });
});
