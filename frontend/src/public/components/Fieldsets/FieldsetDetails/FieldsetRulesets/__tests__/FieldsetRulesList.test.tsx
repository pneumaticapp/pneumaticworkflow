import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldsetRulesList } from '../FieldsetRulesList';
import { intlMock } from '../../../../../__stubs__/intlMock';
import {
  makeFieldsetRuleset,
  makeFieldsetRuleGroupOr,
  makeFieldsetRuleGroupAnd,
} from '../../../../../__stubs__/fieldsets.factory';

jest.mock('../FieldsetRuleItem', () => ({
  FieldsetRuleItem: jest.fn(
    (props: {
      groupAndRule: { apiName: string };
      updateRule: (params: any) => void;
      deleteRule: (params: any) => void;
      regroupRules: (params: any) => void;
    }) =>
      React.createElement(
        'div',
        { 'data-testid': `fieldset-rule-item-${props.groupAndRule.apiName}` },
        React.createElement(
          'button',
          {
            type: 'button',
            'data-testid': `trigger-update-${props.groupAndRule.apiName}`,
            onClick: () =>
              props.updateRule({
                ruleGroupOrApiName: 'g-or-1',
                ruleGroupAndApiName: props.groupAndRule.apiName,
                ruleChanges: { value: '999' },
              }),
          },
          'Update',
        ),
      ),
  ),
}));

describe('FieldsetRulesList component', () => {
  const mockAddRule = jest.fn();
  const mockUpdateRule = jest.fn();
  const mockDeleteRule = jest.fn();
  const mockRegroupRules = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders section label and add rule button when rules list is empty', () => {
    const emptyRuleset = makeFieldsetRuleset({ groupsOr: [] });

    render(
      <FieldsetRulesList
        ruleSet={emptyRuleset}
        isReadOnly={false}
        addRule={mockAddRule}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    expect(screen.getByText(formatMsg('fieldsets.rules'))).toBeInTheDocument();

    const addBtn = screen.getByRole('button', {
      name: formatMsg('fieldsets.add-rule'),
    });
    userEvent.click(addBtn);

    expect(mockAddRule).toHaveBeenCalledTimes(1);
  });

  it('renders FieldsetRuleItem components for each rule in groupsOr', () => {
    const ruleSet = makeFieldsetRuleset({
      groupsOr: [
        makeFieldsetRuleGroupOr({
          groupsAnd: [
            makeFieldsetRuleGroupAnd({ apiName: 'rule-and-1' }),
            makeFieldsetRuleGroupAnd({ apiName: 'rule-and-2' }),
          ],
        }),
      ],
    });

    render(
      <FieldsetRulesList
        ruleSet={ruleSet}
        isReadOnly={false}
        addRule={mockAddRule}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    expect(screen.getByTestId('fieldset-rule-item-rule-and-1')).toBeInTheDocument();
    expect(screen.getByTestId('fieldset-rule-item-rule-and-2')).toBeInTheDocument();

    const addAnotherBtn = screen.getByRole('button', {
      name: formatMsg('fieldsets.add-another-rule'),
    });
    expect(addAnotherBtn).toBeInTheDocument();
  });

  it('correctly passes callbacks down to FieldsetRuleItem', () => {
    const ruleSet = makeFieldsetRuleset({
      groupsOr: [
        makeFieldsetRuleGroupOr({
          groupsAnd: [makeFieldsetRuleGroupAnd({ apiName: 'rule-and-1' })],
        }),
      ],
    });

    render(
      <FieldsetRulesList
        ruleSet={ruleSet}
        isReadOnly={false}
        addRule={mockAddRule}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    const triggerUpdateBtn = screen.getByTestId('trigger-update-rule-and-1');
    userEvent.click(triggerUpdateBtn);

    expect(mockUpdateRule).toHaveBeenCalledTimes(1);
    expect(mockUpdateRule).toHaveBeenCalledWith({
      ruleGroupOrApiName: 'g-or-1',
      ruleGroupAndApiName: 'rule-and-1',
      ruleChanges: { value: '999' },
    });
  });

  it('hides add rule button in read-only mode', () => {
    const emptyRuleset = makeFieldsetRuleset({ groupsOr: [] });

    render(
      <FieldsetRulesList
        ruleSet={emptyRuleset}
        isReadOnly={true}
        addRule={mockAddRule}
        updateRule={mockUpdateRule}
        deleteRule={mockDeleteRule}
        regroupRules={mockRegroupRules}
      />,
    );

    expect(
      screen.queryByRole('button', { name: formatMsg('fieldsets.add-rule') }),
    ).not.toBeInTheDocument();
  });
});
