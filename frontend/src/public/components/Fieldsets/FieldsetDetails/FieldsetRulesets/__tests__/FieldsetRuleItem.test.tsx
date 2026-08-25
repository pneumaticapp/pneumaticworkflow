import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldsetRuleItem } from '../FieldsetRuleItem';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeFieldsetRuleGroupAnd } from '../../../../../__stubs__/fieldsets.factory';
import { EFieldsetNumberRulesetOperator, ERuleCombinator } from '../../../../../types/fieldset';

jest.mock('../../../../UI', () => ({
  FilterSelect: jest.fn(
    (props: {
      options: { apiName: string; name: string }[];
      selectedOption?: string;
      onChange: (val: any) => void;
      isDisabled?: boolean;
    }) =>
      React.createElement(
        'div',
        { 'data-testid': 'filter-select' },
        ...props.options.map((option) =>
          React.createElement(
            'button',
            {
              key: option.apiName,
              type: 'button',
              disabled: props.isDisabled,
              'data-testid': `filter-option-${option.apiName}`,
              onClick: () => props.onChange(option.apiName),
            },
            option.name,
          ),
        ),
      ),
  ),
  SelectMenu: jest.fn(
    (props: {
      activeValue: string;
      values: (string | { id: string; name: string })[];
      onChange: (val: string) => void;
      isDisabled?: boolean;
    }) =>
      React.createElement(
        'select',
        {
          'data-testid': 'select-menu',
          disabled: props.isDisabled,
          value: props.activeValue,
          onChange: (e: any) => props.onChange(e.target.value),
        },
        props.values.map((v) => {
          const val = typeof v === 'string' ? v : v.id;
          const label = typeof v === 'string' ? v : v.name;
          return React.createElement('option', { key: val, value: val }, label);
        }),
      ),
  ),
}));

describe('FieldsetRuleItem component', () => {
  const mockUpdateRule = jest.fn();
  const mockDeleteRule = jest.fn();
  const mockRegroupRules = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const ruleOperatorOptions = [
    { apiName: EFieldsetNumberRulesetOperator.SumEqual, name: 'Sum Equal' },
    { apiName: EFieldsetNumberRulesetOperator.SumGreaterThan, name: 'Sum Greater Than' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders rule value input and calls updateRule on value change', () => {
    const groupAndRule = makeFieldsetRuleGroupAnd({
      apiName: 'rule-and-1',
      operator: EFieldsetNumberRulesetOperator.SumEqual,
      value: '100',
    });

    render(
      <FieldsetRuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="group-or-1"
        groupOrIndex={0}
        groupAndIndex={0}
        ruleOperatorOptions={ruleOperatorOptions}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const input = screen.getByPlaceholderText(
      formatMsg('fieldsets.rule-value-placeholder-number'),
    );
    expect(input).toHaveValue('100');

    fireEvent.change(input, { target: { value: '250' } });

    expect(mockUpdateRule).toHaveBeenCalledTimes(1);
    expect(mockUpdateRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'group-or-1',
      ruleGroupAndApiName: 'rule-and-1',
      ruleChanges: { value: '250' },
    });
  });

  it('calls updateRule with operator when selected via FilterSelect', () => {
    const groupAndRule = makeFieldsetRuleGroupAnd({
      apiName: 'rule-and-1',
      operator: EFieldsetNumberRulesetOperator.SumEqual,
      value: '10',
    });

    render(
      <FieldsetRuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="group-or-1"
        groupOrIndex={0}
        groupAndIndex={0}
        ruleOperatorOptions={ruleOperatorOptions}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const greaterThanOption = screen.getByTestId(
      `filter-option-${EFieldsetNumberRulesetOperator.SumGreaterThan}`,
    );
    userEvent.click(greaterThanOption);

    expect(mockUpdateRule).toHaveBeenCalledTimes(1);
    expect(mockUpdateRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'group-or-1',
      ruleGroupAndApiName: 'rule-and-1',
      ruleChanges: { operator: EFieldsetNumberRulesetOperator.SumGreaterThan },
    });
  });

  it('calls deleteRule when delete button is clicked', () => {
    const groupAndRule = makeFieldsetRuleGroupAnd({
      apiName: 'rule-and-1',
    });

    render(
      <FieldsetRuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="group-or-1"
        groupOrIndex={0}
        groupAndIndex={0}
        ruleOperatorOptions={ruleOperatorOptions}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const deleteBtn = screen.getByRole('button', {
      name: formatMsg('fieldsets.rule-delete'),
    });
    userEvent.click(deleteBtn);

    expect(mockDeleteRule).toHaveBeenCalledTimes(1);
    expect(mockDeleteRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'group-or-1',
      ruleGroupAndApiName: 'rule-and-1',
    });
  });

  it('renders combinator select for non-first rules and calls regroupRules on change', () => {
    const groupAndRule = makeFieldsetRuleGroupAnd({
      apiName: 'rule-and-2',
    });

    render(
      <FieldsetRuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="group-or-1"
        groupOrIndex={0}
        groupAndIndex={1}
        ruleOperatorOptions={ruleOperatorOptions}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const combinatorSelect = screen.getByTestId('select-menu');
    fireEvent.change(combinatorSelect, { target: { value: ERuleCombinator.Or } });

    expect(mockRegroupRules).toHaveBeenCalledTimes(1);
    expect(mockRegroupRules).toHaveBeenCalledWith({
      groupOrApiName: 'group-or-1',
      groupAndApiName: 'rule-and-2',
      ruleCombinator: ERuleCombinator.Or,
    });
  });
});
