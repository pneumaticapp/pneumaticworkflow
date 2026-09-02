import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
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
  FilterSelect: (props: {
    options?: { apiName: string; name: string }[];
    selectedOption?: string;
    placeholderText?: string;
    isDisabled?: boolean;
    onChange: (value: string) => void;
  }) => (
    <select
      data-testid="filter-select-operator"
      disabled={props.isDisabled}
      value={props.selectedOption || ''}
      onChange={(event) => {
        props.onChange(event.target.value);
      }}
    >
      {props.options?.map((option) => (
        <option key={option.apiName} value={option.apiName}>
          {option.name}
        </option>
      ))}
    </select>
  ),
}));

describe('RuleOperatorSelect component', () => {
  it('renders operator options and triggers onChange when selected', () => {
    const handleChange = jest.fn();

    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Text}
        operator="equal"
        isReadOnly={false}
        onChange={handleChange}
      />,
    );

    const select = screen.getByTestId('filter-select-operator');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('equal');

    fireEvent.change(select, { target: { value: 'not_equals' } });

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('not_equals', false);
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

    const select = screen.getByTestId('filter-select-operator');
    expect(select).toBeDisabled();
  });

  it('passes isWithoutValue=true when selecting an operator without value', () => {
    const handleChange = jest.fn();

    render(
      <RuleOperatorSelect
        fieldType={EExtraFieldType.Text}
        operator="equal"
        isReadOnly={false}
        onChange={handleChange}
      />,
    );

    const select = screen.getByTestId('filter-select-operator');
    fireEvent.change(select, { target: { value: 'exists' } });

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('exists', true);
  });
});
