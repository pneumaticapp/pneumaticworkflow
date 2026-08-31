import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { RuleItemValidator } from '../RuleItemValidator';
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

describe('RuleItemValidator component', () => {
  const mockGroupAndRule: IBaseRuleGroupAnd = {
    apiName: 'and_1',
    operator: 'regex',
    value: '^[0-9]+$',
  };

  const mockOperatorOptions = [
    { apiName: 'regex', name: 'Regular expression' },
    { apiName: 'min_length', name: 'Min length' },
  ];

  it('triggers updateRule when operator is changed', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemValidator
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRulesetBaseOperatorOptions={mockOperatorOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const select = screen.getByTestId('filter-select');
    fireEvent.change(select, { target: { value: 'min_length' } });

    expect(handleUpdateRule).toHaveBeenCalledTimes(1);
    expect(handleUpdateRule).toHaveBeenCalledWith({
      groupOrApiName: 'or_1',
      groupAndApiName: 'and_1',
      ruleChanges: {
        operator: 'min_length',
      },
    });
  });

  it('triggers updateRule when text value is changed', () => {
    const handleUpdateRule = jest.fn();

    render(
      <RuleItemValidator
        groupAndRule={mockGroupAndRule}
        groupOrApiName="or_1"
        fieldRulesetBaseOperatorOptions={mockOperatorOptions}
        updateRule={handleUpdateRule}
      />,
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: '^[a-z]+$' } });

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
    const emptyValueRule: IBaseRuleGroupAnd = {
      apiName: 'and_1',
      operator: 'regex',
      value: '',
    };

    render(
      <RuleItemValidator
        groupAndRule={emptyValueRule}
        groupOrApiName="or_1"
        fieldRulesetBaseOperatorOptions={mockOperatorOptions}
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
});
