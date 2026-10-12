import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { RulesetFieldsSelector } from '../RulesetFieldsSelector';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeFieldsetRuleset } from '../../../../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EExtraFieldType } from '../../../../../types/template';
import { FilterSelect } from '../../../../UI';

function requireJestMock(value: unknown, label: string): jest.Mock {
  if (!jest.isMockFunction(value)) {
    throw new Error(`${label} is not a jest.Mock`);
  }
  return value;
}

jest.mock('react-intl', () => ({
  ...jest.requireActual('react-intl'),
  useIntl: () => intlMock,
}));

jest.mock('../../../../UI', () => ({
  FilterSelect: jest.fn((props: {
    options: { apiName: string; name: string }[];
    selectedOptions: (string | number | null)[];
    onChange: (vals: (string | number | null)[]) => void;
    resetFilter?: () => void;
    placeholderText?: string;
    renderPlaceholder?: (opts?: unknown) => React.ReactNode;
    isDisabled?: boolean;
    selectAllLabel?: string;
  }) =>
    React.createElement(
      'div',
      {
        'data-testid': 'filter-select',
        'data-disabled': props.isDisabled ? 'true' : 'false',
      },
      React.createElement(
        'span',
        { 'data-testid': 'filter-placeholder' },
        props.renderPlaceholder ? props.renderPlaceholder() : props.placeholderText,
      ),
      ...props.options.map((opt) =>
        React.createElement(
          'button',
          {
            key: opt.apiName,
            type: 'button',
            'data-testid': `filter-option-${opt.apiName}`,
            onClick: () => {
              const current = props.selectedOptions || [];
              const next = current.includes(opt.apiName)
                ? current.filter((id) => id !== opt.apiName)
                : [...current, opt.apiName];
              props.onChange(next);
            },
          },
          opt.name,
        ),
      ),
      React.createElement(
        'button',
        {
          type: 'button',
          'data-testid': 'filter-reset',
          onClick: props.resetFilter,
        },
        'Reset',
      ),
    ),
  ),
  Tooltip: jest.fn(({ children, content, disabled }: { children: React.ReactNode; content: React.ReactNode; disabled?: boolean }) =>
    React.createElement(
      'div',
      {
        'data-testid': 'tooltip-wrapper',
        'data-tooltip-content': String(content),
        'data-tooltip-disabled': disabled ? 'true' : 'false',
      },
      children,
    ),
  ),
}));

jest.mock('../../../../icons', () => ({
  DeleteRoundIcon: () => React.createElement('span', { 'data-testid': 'delete-round-icon' }),
}));

describe('RulesetFieldsSelector component', () => {
  const mockOnRulesetsChange = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const numField1 = makeExtraField({
    apiName: 'num-1',
    name: 'Total',
    type: EExtraFieldType.Number,
  });
  const numField2 = makeExtraField({
    apiName: 'num-2',
    name: 'Discount',
    type: EExtraFieldType.Number,
  });
  const textField = makeExtraField({
    apiName: 'text-1',
    name: 'Comment',
    type: EExtraFieldType.String,
  });

  const allFields = [numField1, numField2, textField];
  const numericFields = [numField1, numField2];

  const defaultRuleSet = makeFieldsetRuleset({
    apiName: 'rule-set-1',
    fields: [],
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders label and FilterSelect with placeholder', () => {
    render(
      <RulesetFieldsSelector
        ruleSet={defaultRuleSet}
        rulesets={[defaultRuleSet]}
        fields={allFields}
        numericFields={numericFields}
        onRulesetsChange={mockOnRulesetsChange}
      />,
    );

    expect(screen.getByText(formatMsg('fieldsets.rule-fields'))).toBeInTheDocument();
    expect(screen.getByTestId('filter-placeholder')).toHaveTextContent(
      formatMsg('fieldsets.rule-fields-placeholder'),
    );
  });

  it('does not pass selectAllLabel to FilterSelect', () => {
    render(
      <RulesetFieldsSelector
        ruleSet={defaultRuleSet}
        rulesets={[defaultRuleSet]}
        fields={allFields}
        numericFields={numericFields}
        onRulesetsChange={mockOnRulesetsChange}
      />,
    );

    const filterSelectMock = requireJestMock(FilterSelect, 'FilterSelect');
    const lastProps = filterSelectMock.mock.calls[filterSelectMock.mock.calls.length - 1][0];
    expect(lastProps).not.toHaveProperty('selectAllLabel');
  });

  it('calls onRulesetsChange when selecting options in FilterSelect', () => {
    render(
      <RulesetFieldsSelector
        ruleSet={defaultRuleSet}
        rulesets={[defaultRuleSet]}
        fields={allFields}
        numericFields={numericFields}
        onRulesetsChange={mockOnRulesetsChange}
      />,
    );

    userEvent.click(screen.getByTestId('filter-option-num-1'));

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
    const updated = mockOnRulesetsChange.mock.calls[0][0];
    expect(updated[0].fields).toEqual(['num-1']);
  });

  it('calls onRulesetsChange with empty fields when resetFilter is called', () => {
    const rulesetWithFields = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      fields: ['num-1'],
    });

    render(
      <RulesetFieldsSelector
        ruleSet={rulesetWithFields}
        rulesets={[rulesetWithFields]}
        fields={allFields}
        numericFields={numericFields}
        onRulesetsChange={mockOnRulesetsChange}
      />,
    );

    userEvent.click(screen.getByTestId('filter-reset'));

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
    const updated = mockOnRulesetsChange.mock.calls[0][0];
    expect(updated[0].fields).toEqual([]);
  });

  it('renders selected field tags and removes a field on tag close click', () => {
    const rulesetWithFields = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      fields: ['num-1', 'num-2'],
    });

    render(
      <RulesetFieldsSelector
        ruleSet={rulesetWithFields}
        rulesets={[rulesetWithFields]}
        fields={allFields}
        numericFields={numericFields}
        onRulesetsChange={mockOnRulesetsChange}
      />,
    );

    expect(screen.getAllByText('Total').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Discount').length).toBeGreaterThan(0);

    const deleteButtons = screen.getAllByRole('button', {
      name: formatMsg('fieldsets.rule-delete'),
    });
    expect(deleteButtons).toHaveLength(2);

    userEvent.click(deleteButtons[0]);

    expect(mockOnRulesetsChange).toHaveBeenCalledTimes(1);
    const updated = mockOnRulesetsChange.mock.calls[0][0];
    expect(updated[0].fields).toEqual(['num-2']);
  });

  it('disables FilterSelect and hides tag close buttons when isReadOnly=true', () => {
    const rulesetWithFields = makeFieldsetRuleset({
      apiName: 'rule-set-1',
      fields: ['num-1'],
    });

    render(
      <RulesetFieldsSelector
        ruleSet={rulesetWithFields}
        rulesets={[rulesetWithFields]}
        fields={allFields}
        numericFields={numericFields}
        onRulesetsChange={mockOnRulesetsChange}
        isReadOnly={true}
      />,
    );

    expect(screen.getByTestId('filter-select')).toHaveAttribute('data-disabled', 'true');
    expect(
      screen.queryByRole('button', { name: formatMsg('fieldsets.rule-delete') }),
    ).not.toBeInTheDocument();
  });

  it('disables FilterSelect and enables tooltip when numericFields is empty', () => {
    render(
      <RulesetFieldsSelector
        ruleSet={defaultRuleSet}
        rulesets={[defaultRuleSet]}
        fields={allFields}
        numericFields={[]}
        onRulesetsChange={mockOnRulesetsChange}
      />,
    );

    expect(screen.getByTestId('filter-select')).toHaveAttribute('data-disabled', 'true');
    expect(screen.getByTestId('tooltip-wrapper')).toHaveAttribute('data-tooltip-disabled', 'false');
  });
});
