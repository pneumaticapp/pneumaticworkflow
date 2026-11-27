import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RuleItemFieldOperatorValue } from '../RuleItemFieldOperatorValue';
import { EExtraFieldType } from '../../../../../types/template';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EFieldRuleOperator, EFieldRuleValueType } from '../../../../../types/fieldset';
import { makeFieldRuleShowGroupAnd } from '../../../../../__stubs__/fieldsets.factory';

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
    fieldType?: string;
    value?: string;
    valueType?: string | null;
    onChange: (value: string, valueType?: string) => void;
  }) => {
    const { EExtraFieldType: FieldType } = require('../../../../../types/template');
    const { EFieldRuleValueType: ValueType } = require('../../../../../types/fieldset');

    return (
      <>
        <input
          data-testid="rule-value-input"
          data-value-type={props.valueType ?? ''}
          value={props.value || ''}
          onChange={(event) => props.onChange(event.target.value)}
        />
        {props.fieldType === FieldType.User && (
          <>
            <button type="button" onClick={() => props.onChange('5', ValueType.Group)}>
              Select group
            </button>
            <button type="button" onClick={() => props.onChange('5', ValueType.User)}>
              Select user
            </button>
          </>
        )}
      </>
    );
  },
}));

describe('RuleItemFieldOperatorValue component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockGroupAndRule = makeFieldRuleShowGroupAnd({
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

  describe('valueType handling in Show rule row', () => {
    const userAndTextOptions = [
      {
        apiName: 'field_user',
        name: 'Assignee',
        type: EExtraFieldType.User,
        selections: [],
      },
      {
        apiName: 'field_text',
        name: 'Comment',
        type: EExtraFieldType.Text,
        selections: [],
      },
    ];

    const userGroupRule = makeFieldRuleShowGroupAnd({
      apiName: 'and_1',
      field: 'field_user',
      operator: EFieldRuleOperator.Equal,
      value: '1',
      valueType: EFieldRuleValueType.Group,
    });

    it('passes rule valueType to RuleValueInput', () => {
      render(
        <RuleItemFieldOperatorValue
          groupAndRule={userGroupRule}
          groupOrApiName="or_1"
          fieldRuleShowFieldOptions={userAndTextOptions}
          updateRule={jest.fn()}
        />,
      );

      const valueInput = screen.getByTestId('rule-value-input');

      expect(valueInput).toHaveAttribute('data-value-type', EFieldRuleValueType.Group);
    });

    it('saves value and valueType=Group when selecting a group', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemFieldOperatorValue
          groupAndRule={{ ...userGroupRule, value: '', valueType: null }}
          groupOrApiName="or_1"
          fieldRuleShowFieldOptions={userAndTextOptions}
          updateRule={handleUpdateRule}
        />,
      );

      userEvent.click(screen.getByRole('button', { name: 'Select group' }));

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          value: '5',
          valueType: EFieldRuleValueType.Group,
        },
      });
    });

    it('saves value and valueType=User when selecting a user', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemFieldOperatorValue
          groupAndRule={{ ...userGroupRule, value: '', valueType: null }}
          groupOrApiName="or_1"
          fieldRuleShowFieldOptions={userAndTextOptions}
          updateRule={handleUpdateRule}
        />,
      );

      userEvent.click(screen.getByRole('button', { name: 'Select user' }));

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          value: '5',
          valueType: EFieldRuleValueType.User,
        },
      });
    });

    it('omits valueType from ruleChanges when updating a non-User field value', () => {
      const handleUpdateRule = jest.fn();
      const textRuleWithServerNull = makeFieldRuleShowGroupAnd({
        apiName: 'and_1',
        field: 'field_text',
        operator: EFieldRuleOperator.Equal,
        value: '',
        valueType: null,
      });

      render(
        <RuleItemFieldOperatorValue
          groupAndRule={textRuleWithServerNull}
          groupOrApiName="or_1"
          fieldRuleShowFieldOptions={userAndTextOptions}
          updateRule={handleUpdateRule}
        />,
      );

      const valueInput = screen.getByTestId('rule-value-input');
      userEvent.paste(valueInput, 'hello');

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          value: 'hello',
        },
      });
      expect(handleUpdateRule.mock.calls[0][0].ruleChanges).not.toHaveProperty('valueType');
    });

    it('resets valueType to null when switching from a User field to another field', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemFieldOperatorValue
          groupAndRule={userGroupRule}
          groupOrApiName="or_1"
          fieldRuleShowFieldOptions={userAndTextOptions}
          updateRule={handleUpdateRule}
        />,
      );

      const fieldSelect = screen.getByTestId('filter-select');
      userEvent.selectOptions(fieldSelect, 'field_text');

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          field: 'field_text',
          operator: null,
          value: '',
          valueType: null,
        },
      });
    });

    it('resets valueType to null when changing operator to Exist', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemFieldOperatorValue
          groupAndRule={{ ...userGroupRule, valueType: EFieldRuleValueType.User }}
          groupOrApiName="or_1"
          fieldRuleShowFieldOptions={userAndTextOptions}
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

    it('resets valueType to null when changing operator to NotExist', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemFieldOperatorValue
          groupAndRule={userGroupRule}
          groupOrApiName="or_1"
          fieldRuleShowFieldOptions={userAndTextOptions}
          updateRule={handleUpdateRule}
        />,
      );

      const operatorSelect = screen.getByRole('combobox', { name: 'operator' });
      userEvent.selectOptions(operatorSelect, EFieldRuleOperator.NotExist);

      expect(handleUpdateRule).toHaveBeenCalledTimes(1);
      expect(handleUpdateRule).toHaveBeenCalledWith({
        groupOrApiName: 'or_1',
        groupAndApiName: 'and_1',
        ruleChanges: {
          operator: EFieldRuleOperator.NotExist,
          value: '',
          valueType: null,
        },
      });
    });

    it('preserves valueType when switching to another operator that expects a value', () => {
      const handleUpdateRule = jest.fn();

      render(
        <RuleItemFieldOperatorValue
          groupAndRule={userGroupRule}
          groupOrApiName="or_1"
          fieldRuleShowFieldOptions={userAndTextOptions}
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
  });
});
