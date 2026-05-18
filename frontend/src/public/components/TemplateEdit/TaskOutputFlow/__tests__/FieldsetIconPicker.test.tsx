// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { IFieldsetData } from '../../../../types/template';
import { intlMock } from '../../../../__stubs__/intlMock';
import { Dropdown } from '../../../UI';
import { FieldsetIconPicker, IFieldsetIconPickerProps } from '../FieldsetIconPicker';

jest.mock('../../../UI', () => ({
  Dropdown: jest.fn((props: any) => props.options?.customSubOption ?? null),
  CustomTooltip: () => null,
}));

jest.mock('../../../UI/CustomTooltip', () => ({
  CustomTooltip: () => null,
}));

jest.mock('../../../icons/FieldsetIcon', () => ({
  FieldsetIcon: () => null,
}));

const makeFieldsetData = (
  id: number,
  apiName: string,
  name: string,
  order: number,
): IFieldsetData => ({
  id,
  apiName,
  name,
  description: '',
  order,
  fields: [],
  rulesCount: 0,
} as IFieldsetData);

const getDropdownProps = () => {
  const calls = (Dropdown as jest.Mock).mock.calls;
  return calls[calls.length - 1][0];
};

const formatMsg = (id: string, defaultMessage?: string) =>
  intlMock.formatMessage({ id, defaultMessage });

describe('FieldsetIconPicker', () => {
  const makeProps = (overrides: Partial<IFieldsetIconPickerProps> = {}): IFieldsetIconPickerProps => ({
    templateId: 1,
    fieldsetsByApiName: new Map(),
    fieldsetsCatalogLoading: false,
    selectedFieldsetApiNames: [],
    onSelectFieldset: jest.fn(),
    onRemoveFieldset: jest.fn(),
    ...overrides,
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('templateId=undefined → Dropdown receives isDisabled: true', () => {
    render(React.createElement(FieldsetIconPicker, makeProps({ templateId: undefined })));
    expect(getDropdownProps().isDisabled).toBe(true);
  });

  it('templateId=number → Dropdown receives isDisabled: false', () => {
    render(React.createElement(FieldsetIconPicker, makeProps({ templateId: 42 })));
    expect(getDropdownProps().isDisabled).toBe(false);
  });

  it('fieldsetsCatalogLoading=true and empty catalog → loading text is rendered', () => {
    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({ fieldsetsCatalogLoading: true, fieldsetsByApiName: new Map() }),
      ),
    );
    expect(
      screen.getByText(formatMsg('template.fieldset-picker.loading', 'Loading…')),
    ).toBeInTheDocument();
  });

  it('fieldsetsCatalogLoading=false and empty catalog → empty text is rendered', () => {
    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({ fieldsetsCatalogLoading: false, fieldsetsByApiName: new Map() }),
      ),
    );
    expect(screen.getByText(formatMsg('template.fieldset-picker.empty'))).toBeInTheDocument();
  });

  it('renders fieldsets sorted by order property', () => {
    const map = new Map<string, IFieldsetData>([
      ['fs-a', makeFieldsetData(1, 'fs-a', 'Alpha', 2)],
      ['fs-b', makeFieldsetData(2, 'fs-b', 'Zeta', 0)],
      ['fs-c', makeFieldsetData(3, 'fs-c', 'Beta', 1)],
    ]);

    render(React.createElement(FieldsetIconPicker, makeProps({ fieldsetsByApiName: map })));

    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveTextContent('Zeta');
    expect(buttons[1]).toHaveTextContent('Beta');
    expect(buttons[2]).toHaveTextContent('Alpha');
  });

  it('click on unselected fieldset calls onSelectFieldset, onRemoveFieldset not called', () => {
    const onSelectFieldset = jest.fn();
    const onRemoveFieldset = jest.fn();
    const map = new Map<string, IFieldsetData>([
      ['fs-1', makeFieldsetData(1, 'fs-1', 'My Fieldset', 0)],
    ]);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          fieldsetsByApiName: map,
          selectedFieldsetApiNames: [],
          onSelectFieldset,
          onRemoveFieldset,
        }),
      ),
    );

    userEvent.click(screen.getByRole('button'));

    expect(onSelectFieldset).toHaveBeenCalledTimes(1);
    expect(onSelectFieldset).toHaveBeenCalledWith('fs-1');
    expect(onRemoveFieldset).not.toHaveBeenCalled();
  });

  it('click on selected fieldset calls onRemoveFieldset, onSelectFieldset not called', () => {
    const onSelectFieldset = jest.fn();
    const onRemoveFieldset = jest.fn();
    const map = new Map<string, IFieldsetData>([
      ['fs-1', makeFieldsetData(1, 'fs-1', 'My Fieldset', 0)],
    ]);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          fieldsetsByApiName: map,
          selectedFieldsetApiNames: ['fs-1'],
          onSelectFieldset,
          onRemoveFieldset,
        }),
      ),
    );

    userEvent.click(screen.getByRole('button'));

    expect(onRemoveFieldset).toHaveBeenCalledTimes(1);
    expect(onRemoveFieldset).toHaveBeenCalledWith('fs-1');
    expect(onSelectFieldset).not.toHaveBeenCalled();
  });

  it('selected fieldset renders checkbox in checked state', () => {
    const map = new Map<string, IFieldsetData>([
      ['fs-1', makeFieldsetData(1, 'fs-1', 'My Fieldset', 0)],
    ]);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          fieldsetsByApiName: map,
          selectedFieldsetApiNames: ['fs-1'],
        }),
      ),
    );

    const checkbox = screen.getByRole('checkbox', { hidden: true });
    expect(checkbox).toBeChecked();
  });
});
