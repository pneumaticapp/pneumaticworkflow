import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { RuleItem } from '../RuleItem';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeFieldsetRuleGroupAnd } from '../../../../../__stubs__/fieldsets.factory';
import { EFieldsetNumberRulesetOperator, ERuleCombinator, EFieldRuleType } from '../../../../../types/fieldset';

const EMPTY_FIELD_OPTIONS: Array<{ apiName: string; name: string }> = [];

jest.mock('react-redux', () => ({
  useSelector: jest.fn(() => EMPTY_FIELD_OPTIONS),
  useDispatch: jest.fn(() => jest.fn()),
}));

jest.mock('../../../../UI', () => ({
  FilterSelect: (props: {
    selectedOption?: string;
    isDisabled?: boolean;
    onChange: (val: string) => void;
    options?: { apiName: string; name: string }[];
  }) => (
    <select
      data-testid="filter-select"
      value={props.selectedOption}
      disabled={props.isDisabled}
      onChange={(event) => props.onChange(event.target.value)}
    >
      {props.options?.map((option) => (
        <option key={option.apiName} value={option.apiName}>
          {option.name}
        </option>
      ))}
    </select>
  ),
  SelectMenu: (props: {
    activeValue?: string;
    isDisabled?: boolean;
    onChange: (val: string) => void;
    values?: string[];
  }) => (
    <select
      data-testid="select-menu"
      value={props.activeValue}
      disabled={props.isDisabled}
      onChange={(event) => props.onChange(event.target.value)}
    >
      {props.values?.map((value) => (
        <option key={value} value={value}>
          {value}
        </option>
      ))}
    </select>
  ),
  Tooltip: ({ children }: { children?: React.ReactNode }) => <>{children}</>,
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
        fieldRulesetBaseOperatorOptions={defaultOperatorOptions}
        ruleType={EFieldRuleType.Validator}
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
        fieldRulesetBaseOperatorOptions={defaultOperatorOptions}
        ruleType={EFieldRuleType.Validator}
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
        fieldRulesetBaseOperatorOptions={defaultOperatorOptions}
        ruleType={EFieldRuleType.Validator}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const input = screen.getByDisplayValue('100');
    fireEvent.change(input, { target: { value: '150' } });

    expect(mockUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'g-or-1',
      groupAndApiName: 'g-and-1',
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
        fieldRulesetBaseOperatorOptions={defaultOperatorOptions}
        ruleType={EFieldRuleType.Validator}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const deleteBtn = screen.getByRole('button', { name: formatMsg('fieldsets.rule-delete') });
    userEvent.click(deleteBtn);

    expect(mockDeleteRule).toHaveBeenCalledWith({
      groupOrApiName: 'g-or-1',
      groupAndApiName: 'g-and-1',
    });
  });

  it('renders field select for Show ruleType', () => {
    const groupAndRule = {
      ...makeFieldsetRuleGroupAnd({
        apiName: 'g-and-1',
        operator: EFieldsetNumberRulesetOperator.SumEqual,
        value: '100',
      }),
      field: 'field-1',
    };

    const fieldRulesetShowFieldOptions = [
      { apiName: 'field-1', name: 'Field 1' },
      { apiName: 'field-2', name: 'Field 2' },
    ];

    render(
      <RuleItem
        groupAndRule={groupAndRule}
        groupOrApiName="g-or-1"
        groupOrIndex={0}
        groupAndIndex={0}
        fieldRulesetBaseOperatorOptions={defaultOperatorOptions}
        fieldRulesetShowFieldOptions={fieldRulesetShowFieldOptions}
        ruleType={EFieldRuleType.Show}
        isReadOnly={false}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const filterSelects = screen.getAllByTestId('filter-select');
    expect(filterSelects).toHaveLength(2);
    expect(filterSelects[0]).toHaveValue('field-1');
  });

});
