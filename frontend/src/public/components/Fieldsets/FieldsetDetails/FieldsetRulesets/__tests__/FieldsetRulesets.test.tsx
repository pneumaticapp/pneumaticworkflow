import * as React from 'react';
import { render, screen } from '@testing-library/react';
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

jest.mock('../../RuleBase', () => ({
  RuleList: jest.fn(
    (props: {
      ruleSet: { apiName: string };
      addRule: () => void;
      updateRule: (params: any) => void;
      deleteRule: (params: any) => void;
      regroupRules: (params: any) => void;
    }) =>
      React.createElement(
        'div',
        { 'data-testid': `mock-fieldset-rules-list-${props.ruleSet.apiName}` },
        React.createElement(
          'button',
          {
            type: 'button',
            'data-testid': `mock-add-rule-${props.ruleSet.apiName}`,
            onClick: () => props.addRule(),
          },
          'Mock Add Rule',
        ),
        React.createElement(
          'button',
          {
            type: 'button',
            'data-testid': `mock-update-rule-${props.ruleSet.apiName}`,
            onClick: () =>
              props.updateRule({
                ruleGroupOrApiName: 'g-or-1',
                ruleGroupAndApiName: 'g-and-1',
                ruleChanges: { value: '500' },
              }),
          },
          'Mock Update Rule',
        ),
        React.createElement(
          'button',
          {
            type: 'button',
            'data-testid': `mock-delete-rule-${props.ruleSet.apiName}`,
            onClick: () =>
              props.deleteRule({
                ruleGroupOrApiName: 'g-or-1',
                ruleGroupAndApiName: 'g-and-1',
              }),
          },
          'Mock Delete Rule',
        ),
        React.createElement(
          'button',
          {
            type: 'button',
            'data-testid': `mock-regroup-rules-${props.ruleSet.apiName}`,
            onClick: () =>
              props.regroupRules({
                groupOrApiName: 'g-or-1',
                groupAndApiName: 'g-and-1',
                ruleCombinator: ERuleCombinator.Or,
              }),
          },
          'Mock Regroup Rules',
        ),
      ),
  ),
  RulesetMessageInput: jest.fn(
    (props: { message?: string | null; onChange: (msg: string) => void; isReadOnly?: boolean }) =>
      React.createElement(
        'div',
        { 'data-testid': 'mock-ruleset-message-input', 'data-is-readonly': props.isReadOnly },
        React.createElement(
          'button',
          {
            type: 'button',
            'data-testid': 'mock-change-message-btn',
            onClick: () => props.onChange('New message'),
          },
          'Change Message',
        ),
      ),
  ),
}));

jest.mock('../../../../UI', () => ({
  FilterSelect: jest.fn(() => React.createElement('div', { 'data-testid': 'filter-select' })),
  SelectMenu: jest.fn(() => React.createElement('div', { 'data-testid': 'select-menu' })),
  Tooltip: jest.fn(({ children }) => children),
}));

describe('FieldsetRulesets container component', () => {
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

  it('renders ruleset card with mocked RulesetMessageInput and delegates message changes', () => {
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

    expect(screen.getByTestId('mock-fieldset-rules-list-rule-set-1')).toBeInTheDocument();
    expect(screen.getByTestId('mock-ruleset-message-input')).toBeInTheDocument();

    const changeMsgBtn = screen.getByTestId('mock-change-message-btn');
    userEvent.click(changeMsgBtn);

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
    const updated = mockOnRulesetsChange.mock.calls[0][0];
    expect(updated[0].message).toBe('New message');
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
    expect(screen.getByTestId('mock-ruleset-message-input')).toHaveAttribute(
      'data-is-readonly',
      'true',
    );

    expect(
      screen.queryByRole('button', { name: formatMsg('fieldsets.ruleset-delete') }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: new RegExp(formatMsg('fieldsets.add-ruleset'), 'i') }),
    ).not.toBeInTheDocument();
  });

  it('delegates addRule handler to FieldsetRulesList and updates rulesets state', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      groupsOr: [],
    });

    render(
      <FieldsetRulesets
        rulesets={[ruleset]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    const mockAddRuleBtn = screen.getByTestId('mock-add-rule-rule-set-1');
    userEvent.click(mockAddRuleBtn);

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
  });

  it('delegates updateRule handler to FieldsetRulesList and updates rulesets state', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      groupsOr: [
        makeFieldsetRuleGroupOr({
          apiName: 'g-or-1',
          groupsAnd: [
            makeFieldsetRuleGroupAnd({
              apiName: 'g-and-1',
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

    const mockUpdateRuleBtn = screen.getByTestId('mock-update-rule-rule-set-1');
    userEvent.click(mockUpdateRuleBtn);

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
    const updatedRulesets = mockOnRulesetsChange.mock.calls[0][0];
    expect(updatedRulesets[0].groupsOr[0].groupsAnd[0].value).toBe('500');
  });

  it('delegates deleteRule handler to FieldsetRulesList and updates rulesets state', () => {
    const ruleset = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      groupsOr: [
        makeFieldsetRuleGroupOr({
          apiName: 'g-or-1',
          groupsAnd: [
            makeFieldsetRuleGroupAnd({
              apiName: 'g-and-1',
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

    const mockDeleteRuleBtn = screen.getByTestId('mock-delete-rule-rule-set-1');
    userEvent.click(mockDeleteRuleBtn);

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
  });

  it('delegates regroupRules handler to FieldsetRulesList and updates rulesets state', () => {
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

    const mockRegroupBtn = screen.getByTestId('mock-regroup-rules-rule-set-1');
    userEvent.click(mockRegroupBtn);

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
  });
});
