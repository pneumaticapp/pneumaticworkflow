import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RawIntlProvider, createIntl, createIntlCache } from 'react-intl';

import { FieldRuleModal } from '../FieldRuleModal';
import { enMessages } from '../../../../../lang/locales/en_US';

import { EFieldRuleType } from '../../../../../types/fieldset';
import { createEmptyFieldRuleSet } from '../utils';

const cache = createIntlCache();
const intl = createIntl({ locale: 'en-US', messages: enMessages }, cache);

const renderWithIntl = (component: React.ReactNode) => {
  return render(<RawIntlProvider value={intl}>{component}</RawIntlProvider>);
};

describe('FieldRuleModal', () => {
  const defaultProps = {
    isOpen: true,
    ruleset: createEmptyFieldRuleSet(EFieldRuleType.Show),
    onSave: jest.fn(),
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders modal with correct header title and buttons (Discard, Save) when open', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} />);

    expect(screen.getByText('Field rules')).toBeInTheDocument();

    const buttons = screen.getAllByRole('button');
    const buttonLabels = buttons.map((btn) => btn.textContent?.trim());

    expect(buttonLabels).toContain('Discard');
    expect(buttonLabels).toContain('Save');
    expect(buttonLabels).not.toContain('Delete rules');
  });

  it('does not render when isOpen is false', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByText('Field rules')).not.toBeInTheDocument();
  });

  it('calls onSave when Save button is clicked', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} />);

    userEvent.click(screen.getByText('Save'));
    expect(defaultProps.onSave).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Discard button is clicked', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} />);

    userEvent.click(screen.getByText('Discard'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('creates empty ruleset with Show type when ruleset prop is null', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} ruleset={null} />);

    expect(screen.getByText('Field rules')).toBeInTheDocument();
    expect(screen.queryByPlaceholderText('Custom error message...')).not.toBeInTheDocument();
  });

  it('shows message input when ruleset type is Validator', () => {
    const validatorRuleset = createEmptyFieldRuleSet(EFieldRuleType.Validator);
    renderWithIntl(<FieldRuleModal {...defaultProps} ruleset={validatorRuleset} />);

    expect(screen.getByPlaceholderText('Custom error message...')).toBeInTheDocument();
  });
});
