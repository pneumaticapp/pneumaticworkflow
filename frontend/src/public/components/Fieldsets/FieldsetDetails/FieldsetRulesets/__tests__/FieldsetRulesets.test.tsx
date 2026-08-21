import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldsetRulesets } from '../FieldsetRulesets';
import { intlMock } from '../../../../../__stubs__/intlMock';
import {
  makeFieldsetRuleset,
  makeFieldsetRuleGroupOr,
  makeFieldsetRuleGroupAnd,
} from '../../../../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EExtraFieldType } from '../../../../../types/template';
import { EFieldsetNumberRulesetOperator, ERuleCombinator } from '../../../../../types/fieldset';

jest.mock('../../../../UI', () => ({
  FilterSelect: jest.fn(
    (props: {
      options: { apiName: string; name: string }[];
      selectedOptions?: (string | number | null)[];
      selectedOption?: string;
      onChange: (val: any) => void;
      renderPlaceholder?: (opts: any) => React.ReactNode;
      placeholderText?: string;
      isDisabled?: boolean;
    }) =>
      React.createElement(
        'div',
        { 'data-testid': 'filter-select' },
        React.createElement(
          'span',
          { 'data-testid': 'filter-placeholder' },
          props.renderPlaceholder
            ? props.renderPlaceholder(props.options)
            : props.placeholderText,
        ),
        ...props.options.map((option) =>
          React.createElement(
            'button',
            {
              key: option.apiName,
              type: 'button',
              disabled: props.isDisabled,
              'data-testid': `filter-option-${option.apiName}`,
              onClick: () => {
                if (props.selectedOptions) {
                  const selected = props.selectedOptions || [];
                  const isSelected = selected.includes(option.apiName);
                  const next = isSelected
                    ? selected.filter((value) => value !== option.apiName)
                    : [...selected, option.apiName];
                  props.onChange(next);
                } else {
                  props.onChange(option.apiName);
                }
              },
            },
            option.name,
          ),
        ),
      ),
  ),
  SelectMenu: jest.fn(
    (props: {
      activeValue: string;
      values: { id: string; name: string }[];
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
        props.values.map((v) =>
          React.createElement('option', { key: v.id, value: v.id }, v.name),
        ),
      ),
  ),
  Tooltip: jest.fn(({ children }) => children),
}));

describe('FieldsetRulesets component', () => {
  const mockOnRulesetsChange = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const numField1 = makeExtraField({
    apiName: 'num-1',
    name: 'Number Field 1',
    type: EExtraFieldType.Number,
  });
  const numField2 = makeExtraField({
    apiName: 'num-2',
    name: 'Number Field 2',
    type: EExtraFieldType.Number,
  });
  const textField = makeExtraField({
    apiName: 'text-1',
    name: 'Text Field',
    type: EExtraFieldType.String,
  });

  const defaultFields = [numField1, numField2, textField];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders empty state when rulesets array is empty', () => {
    render(
      <FieldsetRulesets
        rulesets={[]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    expect(screen.getByText(formatMsg('fieldsets.no-rules'))).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: new RegExp(formatMsg('fieldsets.add-ruleset'), 'i') }),
    ).toBeInTheDocument();
  });

  it('renders rulesets list and allows updating custom message', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      message: 'Test message',
      fields: ['num-1'],
    });

    render(
      <FieldsetRulesets
        rulesets={[ruleset]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    const messageInput = screen.getByPlaceholderText(
      formatMsg('fieldsets.ruleset-message-placeholder'),
    );
    expect(messageInput).toHaveValue('Test message');

    userEvent.clear(messageInput);
    userEvent.type(messageInput, 'New message');

    expect(mockOnRulesetsChange).toHaveBeenCalled();
  });

  it('calls addRuleset callback on clicking add ruleset button', () => {
    render(
      <FieldsetRulesets
        rulesets={[]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    const addBtn = screen.getByRole('button', {
      name: new RegExp(formatMsg('fieldsets.add-ruleset'), 'i'),
    });
    userEvent.click(addBtn);

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
    expect(mockOnRulesetsChange.mock.calls[0][0]).toHaveLength(1);
  });

  it('calls deleteRuleset callback on clicking delete ruleset button', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      message: 'Error message',
    });

    render(
      <FieldsetRulesets
        rulesets={[ruleset]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    const deleteBtn = screen.getByRole('button', {
      name: formatMsg('fieldsets.ruleset-delete'),
    });
    userEvent.click(deleteBtn);

    expect(mockOnRulesetsChange).toHaveBeenCalledWith([]);
  });

  it('disables controls and displays readonly badge when isReadOnly is true', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      message: 'Read-only message',
    });

    render(
      <FieldsetRulesets
        rulesets={[ruleset]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={true}
      />,
    );

    expect(screen.getByText(formatMsg('fieldsets.readonly-badge'))).toBeInTheDocument();

    const messageInput = screen.getByPlaceholderText(
      formatMsg('fieldsets.ruleset-message-placeholder'),
    );
    expect(messageInput).toBeDisabled();

    expect(
      screen.queryByRole('button', { name: formatMsg('fieldsets.ruleset-delete') }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: new RegExp(formatMsg('fieldsets.add-ruleset'), 'i') }),
    ).not.toBeInTheDocument();
  });

  it('allows changing target AND rule value via input', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      groupsOr: [
        makeFieldsetRuleGroupOr({
          groupsAnd: [
            makeFieldsetRuleGroupAnd({
              operator: EFieldsetNumberRulesetOperator.SumEqual,
              value: '50',
            }),
          ],
        }),
      ],
    });

    render(
      <FieldsetRulesets
        rulesets={[ruleset]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    const valInput = screen.getByPlaceholderText(
      formatMsg('fieldsets.rule-value-placeholder-number'),
    );
    expect(valInput).toHaveValue('50');

    fireEvent.change(valInput, { target: { value: '150' } });

    expect(mockOnRulesetsChange).toHaveBeenCalled();
  });

  it('allows changing rule operator (SumGreaterThan, SumLessThan) via FilterSelect', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      groupsOr: [
        makeFieldsetRuleGroupOr({
          groupsAnd: [
            makeFieldsetRuleGroupAnd({
              operator: EFieldsetNumberRulesetOperator.SumEqual,
              value: '10',
            }),
          ],
        }),
      ],
    });

    render(
      <FieldsetRulesets
        rulesets={[ruleset]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    const greaterThanBtn = screen.getByTestId(
      `filter-option-${EFieldsetNumberRulesetOperator.SumGreaterThan}`,
    );
    userEvent.click(greaterThanBtn);

    expect(mockOnRulesetsChange).toHaveBeenCalled();
    const updated = mockOnRulesetsChange.mock.calls[0][0];
    expect(updated[0].groupsOr[0].groupsAnd[0].operator).toBe(
      EFieldsetNumberRulesetOperator.SumGreaterThan,
    );
  });

  it('allows changing rule combinator (AND / OR) via SelectMenu', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      groupsOr: [
        makeFieldsetRuleGroupOr({
          apiName: 'g-or-1',
          groupsAnd: [
            makeFieldsetRuleGroupAnd({ apiName: 'g-and-1', value: '10' }),
            makeFieldsetRuleGroupAnd({ apiName: 'g-and-2', value: '20' }),
          ],
        }),
      ],
    });

    render(
      <FieldsetRulesets
        rulesets={[ruleset]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    const selectElement = screen.getByTestId('select-menu');
    fireEvent.change(selectElement, { target: { value: ERuleCombinator.Or } });

    expect(mockOnRulesetsChange).toHaveBeenCalled();
  });
});
