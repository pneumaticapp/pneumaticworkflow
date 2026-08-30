import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { RuleList } from '../RuleList';
import { FIELDSET_RULE_OPERATOR_OPTIONS } from '../../../constants';
import { intlMock } from '../../../../../__stubs__/intlMock';
import {
  makeFieldsetRuleset,
  makeFieldsetRuleGroupOr,
  makeFieldsetRuleGroupAnd,
} from '../../../../../__stubs__/fieldsets.factory';

import { EFieldRuleType } from '../../../../../types/fieldset';

jest.mock('../RuleItem', () => ({
  RuleItem: jest.fn((props) => (
    <div data-testid={`mock-rule-item-${props.groupAndRule.apiName}`}>
      <button
        type="button"
        data-testid={`mock-update-${props.groupAndRule.apiName}`}
        onClick={() =>
          props.updateRule({
            ruleGroupOrApiName: props.groupOrApiName,
            ruleGroupAndApiName: props.groupAndRule.apiName,
            ruleChanges: { value: 'updated' },
          })
        }
      >
        Update
      </button>
    </div>
  )),
}));

describe('RuleList component', () => {
  const mockAddRule = jest.fn();
  const mockUpdateRule = jest.fn();
  const mockDeleteRule = jest.fn();
  const mockRegroupRules = jest.fn();

  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders rules label and add rule button', () => {
    const emptyRuleset = makeFieldsetRuleset({ groupsOr: [] });

    render(
      <RuleList
        ruleSet={emptyRuleset}
        ruleType={EFieldRuleType.Validator}
        operatorOptions={FIELDSET_RULE_OPERATOR_OPTIONS}
        isReadOnly={false}
        addRule={mockAddRule}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    expect(screen.getByText(formatMsg('fieldsets.rules'))).toBeInTheDocument();

    const addBtn = screen.getByRole('button', { name: formatMsg('fieldsets.add-rule') });
    expect(addBtn).toBeInTheDocument();

    userEvent.click(addBtn);
    expect(mockAddRule).toHaveBeenCalledTimes(1);
  });

  it('renders RuleItem components for each rule in groupsOr', () => {
    const ruleset = makeFieldsetRuleset({
      groupsOr: [
        makeFieldsetRuleGroupOr({
          apiName: 'g-or-1',
          groupsAnd: [
            makeFieldsetRuleGroupAnd({ apiName: 'rule-1' }),
            makeFieldsetRuleGroupAnd({ apiName: 'rule-2' }),
          ],
        }),
      ],
    });

    render(
      <RuleList
        ruleSet={ruleset}
        ruleType={EFieldRuleType.Validator}
        operatorOptions={FIELDSET_RULE_OPERATOR_OPTIONS}
        isReadOnly={false}
        addRule={mockAddRule}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    expect(screen.getByTestId('mock-rule-item-rule-1')).toBeInTheDocument();
    expect(screen.getByTestId('mock-rule-item-rule-2')).toBeInTheDocument();
  });

  it('correctly passes callbacks down to RuleItem', () => {
    const ruleset = makeFieldsetRuleset({
      groupsOr: [
        makeFieldsetRuleGroupOr({
          apiName: 'g-or-1',
          groupsAnd: [makeFieldsetRuleGroupAnd({ apiName: 'rule-1' })],
        }),
      ],
    });

    render(
      <RuleList
        ruleSet={ruleset}
        ruleType={EFieldRuleType.Validator}
        operatorOptions={FIELDSET_RULE_OPERATOR_OPTIONS}
        isReadOnly={false}
        addRule={mockAddRule}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const updateBtn = screen.getByTestId('mock-update-rule-1');
    userEvent.click(updateBtn);

    expect(mockUpdateRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'g-or-1',
      ruleGroupAndApiName: 'rule-1',
      ruleChanges: { value: 'updated' },
    });
  });

  it('does not render add rule button in readOnly mode', () => {
    const emptyRuleset = makeFieldsetRuleset({ groupsOr: [] });

    render(
      <RuleList
        ruleSet={emptyRuleset}
        ruleType={EFieldRuleType.Validator}
        operatorOptions={FIELDSET_RULE_OPERATOR_OPTIONS}
        isReadOnly={true}
        addRule={mockAddRule}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
