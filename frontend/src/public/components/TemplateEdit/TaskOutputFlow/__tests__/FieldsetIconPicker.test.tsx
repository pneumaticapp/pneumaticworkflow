import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';

import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetCatalogItem } from '../../../../__stubs__/fieldsets.factory';
import { IFieldsetCatalogItem } from '../../../../types/fieldset';
import { intlMock } from '../../../../__stubs__/intlMock';
import { Dropdown } from '../../../UI';
import { IDropdownProps, TDropdownOption } from '../../../UI/Dropdown/Dropdown';
import { FieldsetIconPicker, IFieldsetIconPickerProps } from '../FieldsetIconPicker';
import {
  getFieldsetsCatalogItems,
} from '../../../../redux/selectors/fieldsets';

jest.mock('react-redux', () => ({
  useSelector: jest.fn(),
}));

jest.mock('../../../../redux/selectors/fieldsets', () => ({
  getFieldsetsCatalogItems: jest.fn(() => []),
}));

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


const makeCatalogItem = (
  id: number,
  apiName: string,
  name: string,
  order: number,
): IFieldsetCatalogItem => makeFieldsetCatalogItem({
  id,
  apiName,
  name,
  order,
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

const EMPTY_STATE = {};

describe('FieldsetIconPicker', () => {
  const makeProps = (overrides: Partial<IFieldsetIconPickerProps> = {}): IFieldsetIconPickerProps => ({
    fieldsetsCatalogLoading: false,
    selectedFieldsetIds: [],
    onSelectFieldset: jest.fn(),
    onRemoveFieldset: jest.fn(),
    ...overrides,
  });

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector: unknown) =>
      (selector as (s: unknown) => unknown)(EMPTY_STATE),
    );
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue([]);
  });

  it('Dropdown does not receive isDisabled prop', () => {
    render(React.createElement(FieldsetIconPicker, makeProps()));
    expect(getDropdownProps().isDisabled).toBeUndefined();
  });

  it('fieldsetsCatalogLoading=true and empty catalog → loading text is rendered', () => {
    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({ fieldsetsCatalogLoading: true }),
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
        makeProps({ fieldsetsCatalogLoading: false }),
      ),
    );
    expect(screen.getByText(formatMsg('template.fieldset-picker.empty'))).toBeInTheDocument();
  });

  it('renders fieldsets sorted by order property', () => {
    // Бизнес: филдсеты отображаются в порядке, заданном в каталоге (поле order).
    // Идентификатор: каталожный id (1, 2, 3). Order определяет визуальный порядок.
    const catalogItems: IFieldsetCatalogItem[] = [
      makeCatalogItem(1, 'fs-a', 'Alpha', 2),
      makeCatalogItem(2, 'fs-b', 'Zeta', 0),
      makeCatalogItem(3, 'fs-c', 'Beta', 1),
    ];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(React.createElement(FieldsetIconPicker, makeProps()));

    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveTextContent('Zeta');
    expect(buttons[1]).toHaveTextContent('Beta');
    expect(buttons[2]).toHaveTextContent('Alpha');
  });

  it('click on unselected fieldset calls onSelectFieldset, onRemoveFieldset not called', () => {
    const onSelectFieldset = jest.fn();
    const onRemoveFieldset = jest.fn();
    const catalogItems: IFieldsetCatalogItem[] = [
      makeCatalogItem(1, 'fs-1', 'My Fieldset', 0),
    ];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
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
    const catalogItems: IFieldsetCatalogItem[] = [
      makeCatalogItem(1, 'fs-1', 'My Fieldset', 0),
    ];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
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
    const catalogItems: IFieldsetCatalogItem[] = [
      makeCatalogItem(1, 'fs-1', 'My Fieldset', 0),
    ];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          selectedFieldsetIds: [1],
        }),
      ),
    );

    const checkbox = screen.getByRole('checkbox', { hidden: true });
    expect(checkbox).toBeChecked();
  });

  it('unselected fieldset renders checkbox in unchecked state', () => {
    const catalogItems: IFieldsetCatalogItem[] = [
      makeCatalogItem(1, 'fs-1', 'My Fieldset', 0),
    ];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({
          selectedFieldsetIds: [],
        }),
      ),
    );

    const checkbox = screen.getByRole('checkbox', { hidden: true });
    expect(checkbox).not.toBeChecked();
  });

  it('background catalog load does not show loading text when list is not empty', () => {
    const catalogItems: IFieldsetCatalogItem[] = [
      makeCatalogItem(1, 'fs-1', 'My Set', 0),
    ];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(
      React.createElement(
        FieldsetIconPicker,
        makeProps({ fieldsetsCatalogLoading: true }),
      ),
    );

    expect(
      screen.queryByText(formatMsg('template.fieldset-picker.loading', 'Loading…')),
    ).not.toBeInTheDocument();
    expect(screen.getByText('My Set')).toBeInTheDocument();
  });

  it('meta line shows "<fieldsCount> fields · <rulesCount> rules" with real numbers', () => {
    const catalogItem = makeFieldsetCatalogItem({
      name: 'My Set',
      fields: [makeField('a'), makeField('b'), makeField('c')] as any,
      rules: [{}, {}, {}, {}, {}] as any,
    });
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue([catalogItem]);

    render(React.createElement(FieldsetIconPicker, makeProps()));

    expect(screen.getByText('3 fields · 5 rules')).toBeInTheDocument();
  });

  it('meta line shows "0 fields · 0 rules" when fields and rules are empty', () => {
    const catalogItem = makeFieldsetCatalogItem({
      name: 'My Set',
      fields: [],
      rules: [],
    });
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue([catalogItem]);

    render(React.createElement(FieldsetIconPicker, makeProps()));

    expect(screen.getByText('0 fields · 0 rules')).toBeInTheDocument();
  });
});
