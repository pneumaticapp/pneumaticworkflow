import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RawIntlProvider, createIntl, createIntlCache } from 'react-intl';

import { FieldRuleModal } from '../FieldRuleModal';
import { enMessages } from '../../../../../lang/locales/en_US';

import { EFieldRuleType, EFieldRuleValidatorOperator, IFieldRuleSet } from '../../../../../types/fieldset';
import { EExtraFieldType } from '../../../../../types/template';
import { createEmptyFieldRuleSet } from '../utils';

const cache = createIntlCache();
const intl = createIntl({ locale: 'en-US', messages: enMessages }, cache);

const renderWithIntl = (component: React.ReactNode) => {
  return render(<RawIntlProvider value={intl}>{component}</RawIntlProvider>);
};

describe('FieldRuleModal', () => {
  const mockFieldOption = { apiName: 'field_1', name: 'Field 1', type: EExtraFieldType.Text };

  const validRuleset: IFieldRuleSet = {
    ...createEmptyFieldRuleSet(EFieldRuleType.Show),
    name: 'Test Ruleset',
    groupsOr: [
      {
        apiName: 'or-1',
        groupsAnd: [
          {
            apiName: 'and-1',
            field: 'field_1',
            operator: EFieldRuleValidatorOperator.Equal,
            value: 'test value',
          },
        ],
      },
    ],
  };

  const defaultProps = {
    isOpen: true,
    ruleset: validRuleset,
    fieldType: EExtraFieldType.Number,
    fieldRuleShowFieldOptions: [mockFieldOption],
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
    expect(buttonLabels).not.toContain('Delete ruleset');
  });

  it('does not render when isOpen is false', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByText('Field rules')).not.toBeInTheDocument();
  });

  it('disables Save button when ruleset is invalid', () => {
    const invalidRuleset = createEmptyFieldRuleSet(EFieldRuleType.Show);
    renderWithIntl(<FieldRuleModal {...defaultProps} ruleset={invalidRuleset} />);

    const saveButton = screen.getByText('Save').closest('button');
    expect(saveButton).toBeDisabled();
  });

  it('calls onSave when Save button is clicked on valid ruleset', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} />);

    const saveButton = screen.getByText('Save').closest('button');
    expect(saveButton).not.toBeDisabled();

    userEvent.click(screen.getByText('Save'));
    expect(defaultProps.onSave).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Discard button is clicked', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} />);

    userEvent.click(screen.getByText('Discard'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('creates empty ruleset with default Validator type when ruleset prop is null', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} ruleset={null} />);

    expect(screen.getByText('Field rules')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Custom error message...')).toBeInTheDocument();
  });

  it('shows message input when ruleset type is Validator', () => {
    const validatorRuleset = {
      ...createEmptyFieldRuleSet(EFieldRuleType.Validator),
      name: 'Validator Rule',
    };
    renderWithIntl(<FieldRuleModal {...defaultProps} ruleset={validatorRuleset} />);

    expect(screen.getByPlaceholderText('Custom error message...')).toBeInTheDocument();
  });

  it('highlights name input error on blur and removes error highlight on focus', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} ruleset={{ ...validRuleset, name: '' }} />);

    const nameInput = screen.getByPlaceholderText('Ruleset name...');

    expect(nameInput).not.toHaveClass('ruleset-message-input_error');

    userEvent.click(nameInput);
    userEvent.tab();

    expect(nameInput).toHaveClass('ruleset-message-input_error');

    userEvent.click(nameInput);
    expect(nameInput).not.toHaveClass('ruleset-message-input_error');
  });

  it('renders disabled Show option with tooltip when no field options available', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} fieldRuleShowFieldOptions={[]} />);

    const showElements = screen.getAllByText('Show');
    const disabledOptionText = showElements.find((el) => el.classList.contains('rule-option_disabled'));
    
    expect(disabledOptionText).toBeInTheDocument();
  });

  it('renders prefilled ruleset name when opened in edit mode', () => {
    renderWithIntl(<FieldRuleModal {...defaultProps} ruleset={validRuleset} />);

    const nameInput = screen.getByPlaceholderText('Ruleset name...');
    expect(nameInput).toHaveValue('Test Ruleset');
  });

  it('calls onSave with existing apiName when saving in edit mode', () => {
    const onSave = jest.fn();
    renderWithIntl(
      <FieldRuleModal {...defaultProps} ruleset={validRuleset} onSave={onSave} />,
    );

    userEvent.click(screen.getByText('Save'));

    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ apiName: validRuleset.apiName }),
    );
  });
});
