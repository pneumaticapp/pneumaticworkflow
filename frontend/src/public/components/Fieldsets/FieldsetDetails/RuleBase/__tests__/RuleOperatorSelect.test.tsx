import * as React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RuleOperatorSelect } from '../RuleOperatorSelect';
import { EExtraFieldType } from '../../../../../types/template';
import { intlMock } from '../../../../../__stubs__/intlMock';

jest.mock('react-intl', () => {
  const actualIntl = jest.requireActual('react-intl');
  return {
    ...actualIntl,
    useIntl: () => intlMock,
  };
});

jest.mock('../../../../UI', () => ({
  DropdownList: require('../../../../../__stubs__/uiMocks').DropdownListMock,
}));

describe('RuleOperatorSelect component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders operator select with current operator value', () => {
    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Text}
        operator="equal"
        isReadOnly={false}
        onChange={jest.fn()}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'operator' });
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('equal');
  });

  it('triggers onChange when a different operator is selected', () => {
    const handleChange = jest.fn();

    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Text}
        operator="equal"
        isReadOnly={false}
        onChange={handleChange}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'operator' });
    expect(select).toBeInTheDocument();

    userEvent.selectOptions(select, 'not_equals');

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('not_equals');
  });

  it('renders empty selection when operator is undefined', () => {
    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Text}
        onChange={jest.fn()}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'operator' });
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('');
  });

  it('disables select when isReadOnly is true', () => {
    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Text}
        operator="equal"
        isReadOnly={true}
        onChange={jest.fn()}
      />,
    );

    expect(screen.getByRole('combobox', { name: 'operator' })).toBeDisabled();
  });

  it('enables select when isReadOnly is undefined', () => {
    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Text}
        operator="equal"
        onChange={jest.fn()}
      />,
    );

    expect(screen.getByRole('combobox', { name: 'operator' })).not.toBeDisabled();
  });

  it('does not trigger onChange when re-selecting current operator', () => {
    const handleChange = jest.fn();

    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Text}
        operator="equal"
        isReadOnly={false}
        onChange={handleChange}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'operator' });
    userEvent.selectOptions(select, 'equal');

    expect(handleChange).not.toHaveBeenCalled();
  });

  it('renders numeric ruleset operators when isFieldsetRuleset is true', () => {
    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Number}
        isFieldsetRuleset={true}
        onChange={jest.fn()}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'operator' });
    expect(select).toBeInTheDocument();
    expect(within(select).queryAllByRole('option').length).toBeGreaterThan(0);
  });

  it('renders standard numeric operators when isFieldsetRuleset is false', () => {
    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Number}
        isFieldsetRuleset={false}
        onChange={jest.fn()}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'operator' });
    expect(select).toBeInTheDocument();
    expect(within(select).queryAllByRole('option').length).toBeGreaterThan(0);
  });

  it('renders only placeholder option when fieldType is undefined', () => {
    render(
      <RuleOperatorSelect
        onChange={jest.fn()}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'operator' });
    expect(select).toBeInTheDocument();
    const options = within(select).queryAllByRole('option');
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveValue('');
  });
});
