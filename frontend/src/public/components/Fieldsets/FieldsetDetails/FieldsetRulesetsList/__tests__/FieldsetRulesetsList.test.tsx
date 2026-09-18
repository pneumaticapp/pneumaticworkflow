import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldsetRulesetsList } from '../FieldsetRulesetsList';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeFieldsetRuleset } from '../../../../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EExtraFieldType } from '../../../../../types/template';

jest.mock('../FieldsetRulesetItem', () => ({
  FieldsetRulesetItem: jest.fn((props: { ruleSet: { apiName: string } }) =>
    React.createElement('div', { 'data-testid': `mock-fieldset-ruleset-item-${props.ruleSet.apiName}` }, 'Mock Ruleset Item'),
  ),
}));

describe('FieldsetRulesetsList container component', () => {
  const mockOnRulesetsChange = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const numField1 = makeExtraField({
    apiName: 'num-1',
    name: 'Number Field 1',
    type: EExtraFieldType.Number,
  });
  const textField = makeExtraField({
    apiName: 'text-1',
    name: 'Text Field',
    type: EExtraFieldType.String,
  });

  const defaultFields = [numField1, textField];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders empty state when rulesets array is empty', () => {
    render(
      <FieldsetRulesetsList
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

  it('renders FieldsetRulesetItem for each ruleset in array', () => {
    const ruleset1 = makeFieldsetRuleset({ apiName: 'rule-set-1' });
    const ruleset2 = makeFieldsetRuleset({ apiName: 'rule-set-2' });

    render(
      <FieldsetRulesetsList
        rulesets={[ruleset1, ruleset2]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={false}
      />,
    );

    expect(screen.getByTestId('mock-fieldset-ruleset-item-rule-set-1')).toBeInTheDocument();
    expect(screen.getByTestId('mock-fieldset-ruleset-item-rule-set-2')).toBeInTheDocument();
    expect(screen.queryByText(formatMsg('fieldsets.no-rules'))).not.toBeInTheDocument();
  });

  it('calls addRuleset callback on clicking add ruleset button', () => {
    render(
      <FieldsetRulesetsList
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

  it('displays readonly badge and hides add button when isReadOnly is true', () => {
    render(
      <FieldsetRulesetsList
        rulesets={[]}
        fields={defaultFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={true}
      />,
    );

    expect(screen.getByText(formatMsg('fieldsets.readonly-badge'))).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: new RegExp(formatMsg('fieldsets.add-ruleset'), 'i') }),
    ).not.toBeInTheDocument();
  });
});
