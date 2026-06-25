import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetData as makeFieldsetDataBase } from '../../../../__stubs__/fieldsets.factory';
import { IFieldsetData } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';
import { intlMock } from '../../../../__stubs__/intlMock';
import { Dropdown } from '../../../UI';
import { IDropdownProps, TDropdownOption } from '../../../UI/Dropdown/Dropdown';
import { FieldsetIconPicker, IFieldsetIconPickerProps } from '../FieldsetIconPicker';

jest.mock('../../../UI', () => ({
  Dropdown: jest.fn(({ options }: IDropdownProps) => {
    const single = !Array.isArray(options) ? (options as TDropdownOption) : null;
    return single?.customSubOption ?? null;
  }),
  CustomTooltip: () => null,
}));

jest.mock('../../../UI/CustomTooltip', () => ({
  CustomTooltip: () => null,
}));

jest.mock('../../../icons/FieldsetIcon', () => ({
  FieldsetIcon: () => null,
}));

const makeFieldsetLocalData = (
  id: number,
  apiName: string,
  name: string,
  order: number,
): IFieldsetData => makeFieldsetDataBase({
  id,
  apiName,
  name,
  ...(order !== 0 && { order }),
});

const getDropdownProps = (): IDropdownProps => {
  const calls = (Dropdown as jest.Mock).mock.calls;
  return calls[calls.length - 1][0];
};

const makeField = (apiName: string) => makeExtraField({
  apiName,
  name: `Field ${apiName}`,
});

const formatMsg = (id: string, defaultMessage?: string) =>
  intlMock.formatMessage({ id, defaultMessage });

describe('FieldsetIconPicker', () => {
  const makeProps = (overrides: Partial<IFieldsetIconPickerProps> = {}): IFieldsetIconPickerProps => ({
    templateId: 1,
    fieldsetsByApiName: new Map(),
    fieldsetsCatalogLoading: false,
    selectedFieldsetIds: [],
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
      ['fs-a', makeFieldsetLocalData(1, 'fs-a', 'Alpha', 2)],
      ['fs-b', makeFieldsetLocalData(2, 'fs-b', 'Zeta', 0)],
      ['fs-c', makeFieldsetLocalData(3, 'fs-c', 'Beta', 1)],
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
      ['fs-1', makeFieldsetLocalData(1, 'fs-1', 'My Fieldset', 0)],
    ]);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          fieldsetsByApiName: map,
          selectedFieldsetIds: [],
          onSelectFieldset,
          onRemoveFieldset,
        }),
      ),
    );

    userEvent.click(screen.getByRole('button'));

    expect(onSelectFieldset).toHaveBeenCalledTimes(1);
    expect(onSelectFieldset).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
    expect(onRemoveFieldset).not.toHaveBeenCalled();
  });

  it('click on selected fieldset calls onRemoveFieldset, onSelectFieldset not called', () => {
    const onSelectFieldset = jest.fn();
    const onRemoveFieldset = jest.fn();
    const map = new Map<string, IFieldsetData>([
      ['fs-1', makeFieldsetLocalData(1, 'fs-1', 'My Fieldset', 0)],
    ]);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          fieldsetsByApiName: map,
          selectedFieldsetIds: [1],
          onSelectFieldset,
          onRemoveFieldset,
        }),
      ),
    );

    userEvent.click(screen.getByRole('button'));

    expect(onRemoveFieldset).toHaveBeenCalledTimes(1);
    expect(onRemoveFieldset).toHaveBeenCalledWith(1);
    expect(onSelectFieldset).not.toHaveBeenCalled();
  });

  it('selected fieldset renders checkbox in checked state', () => {
    const map = new Map<string, IFieldsetData>([
      ['fs-1', makeFieldsetLocalData(1, 'fs-1', 'My Fieldset', 0)],
    ]);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          fieldsetsByApiName: map,
          selectedFieldsetIds: [1],
        }),
      ),
    );

    const checkbox = screen.getByRole('checkbox', { hidden: true });
    expect(checkbox).toBeChecked();
  });

  it('unselected fieldset renders checkbox in unchecked state', () => {
    const map = new Map<string, IFieldsetData>([
      ['fs-1', makeFieldsetLocalData(1, 'fs-1', 'My Fieldset', 0)],
    ]);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          fieldsetsByApiName: map,
          selectedFieldsetIds: [],
        }),
      ),
    );

    const checkbox = screen.getByRole('checkbox', { hidden: true });
    expect(checkbox).not.toBeChecked();
  });

  it('background catalog load does not show loading text when list is not empty', () => {
    const map = new Map<string, IFieldsetData>([
      ['fs-1', makeFieldsetLocalData(1, 'fs-1', 'My Set', 0)],
    ]);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({ fieldsetsCatalogLoading: true, fieldsetsByApiName: map }),
      ),
    );

    expect(
      screen.queryByText(formatMsg('template.fieldset-picker.loading', 'Loading…')),
    ).not.toBeInTheDocument();
    expect(screen.getByText('My Set')).toBeInTheDocument();
  });

  it('meta line shows "<fieldsCount> fields · <rulesCount> rules" with real numbers', () => {
    const fieldset: IFieldsetData = makeFieldsetDataBase({
      name: 'My Set',
      fields: [makeField('a'), makeField('b'), makeField('c')],
      rulesCount: 5,
    });
    const map = new Map<string, IFieldsetData>([['fs-1', fieldset]]);

    render(React.createElement(FieldsetIconPicker, makeProps({ fieldsetsByApiName: map })));

    expect(screen.getByText('3 fields · 5 rules')).toBeInTheDocument();
  });

  it('meta line falls back to "0 rules" when rulesCount is undefined', () => {
    const fieldset: IFieldsetData = {
      id: 1,
      apiName: 'fs-1',
      name: 'My Set',
      description: '',
      order: 0,
      labelPosition: EFieldLabelPosition.Top,
      fields: [],
    };
    const map = new Map<string, IFieldsetData>([['fs-1', fieldset]]);

    render(React.createElement(FieldsetIconPicker, makeProps({ fieldsetsByApiName: map })));

    expect(screen.getByText('0 fields · 0 rules')).toBeInTheDocument();
  });
});
