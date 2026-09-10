import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RuleItemOperatorValue } from '../RuleItemOperatorValue';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EFieldRuleOperator } from '../../../../../types/fieldset';
import { EExtraFieldType } from '../../../../../types/template';
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

describe('RuleItemOperatorValue component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockGroupAndRule = makeFieldRuleGroupAnd({
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
    const emptyValueRule = makeFieldRuleGroupAnd({
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
});
