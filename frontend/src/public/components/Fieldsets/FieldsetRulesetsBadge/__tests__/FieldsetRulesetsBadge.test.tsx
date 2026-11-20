import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { FieldsetRulesetsBadge } from '../FieldsetRulesetsBadge';
import { EFieldRuleType } from '../../../../types/fieldset';

jest.mock('../../../IntlMessages', () => ({
  IntlMessages: jest.fn(({ values }: { values?: { count: number } }) =>
    values != null ? String(values.count) : null,
  ),
}));

describe('FieldsetRulesetsBadge', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when count is undefined', () => {
    const { container } = render(<FieldsetRulesetsBadge />);

    expect(container).toBeEmptyDOMElement();
  });

  it('does not render when count is 0', () => {
    const { container } = render(<FieldsetRulesetsBadge count={0} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('does not render when count is negative', () => {
    const { container } = render(<FieldsetRulesetsBadge count={-1} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('renders badge with correct count for 1 ruleset', () => {
    render(<FieldsetRulesetsBadge count={1} />);

    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('renders badge with correct count for multiple rulesets', () => {
    render(<FieldsetRulesetsBadge count={3} />);

    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    render(<FieldsetRulesetsBadge count={1} className="custom-badge-class" />);

    expect(screen.getByTestId('rulesets-badge')).toHaveClass('custom-badge-class');
  });

  it('renders badge from rulesets array length', () => {
    const rulesets = [
      { apiName: 'rs-1', name: 'Rule 1', type: EFieldRuleType.Validator, message: '', groupsOr: [], order: 0 },
      { apiName: 'rs-2', name: 'Rule 2', type: EFieldRuleType.Validator, message: '', groupsOr: [], order: 1 },
    ];

    render(<FieldsetRulesetsBadge rulesets={rulesets} />);

    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('does not render when rulesets is empty array', () => {
    const { container } = render(<FieldsetRulesetsBadge rulesets={[]} />);

    expect(container).toBeEmptyDOMElement();
  });
});
