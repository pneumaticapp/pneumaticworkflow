import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';

import {
  makeFieldsetCatalogItem,
  makeFieldsetField,
  makeFieldsetTemplateRule,
} from '../../../../__stubs__/fieldsets.factory';
import { IFieldsetCatalogItem } from '../../../../types/fieldset';
import { intlMock } from '../../../../__stubs__/intlMock';
import { FieldsetIconPicker, IFieldsetIconPickerProps } from '../FieldsetIconPicker';
import { getFieldsetsCatalogItems } from '../../../../redux/selectors/fieldsets';

jest.mock('react-redux', () => ({
  useSelector: jest.fn(),
}));

jest.mock('../../../../redux/selectors/fieldsets', () => ({
  getFieldsetsCatalogItems: jest.fn(() => []),
}));

jest.mock('../../../UI/CustomTooltip', () => ({
  CustomTooltip: () => null,
}));

jest.mock('../../../icons/FieldsetIcon', () => ({
  FieldsetIcon: () => null,
}));

const makeCatalogItem = (id: number, apiName: string, name: string, order: number): IFieldsetCatalogItem =>
  makeFieldsetCatalogItem({
    id,
    apiName,
    name,
    order,
  });

const formatMsg = (id: string, defaultMessage?: string) => intlMock.formatMessage({ id, defaultMessage });

const EMPTY_STATE = {};

const openPicker = () => userEvent.click(screen.getAllByRole('button')[0]);
const getOptionTexts = () =>
  Array.from(document.querySelectorAll('.react-select__option')).map((option) => option.textContent);

describe('FieldsetIconPicker', () => {
  const makeProps = (overrides: Partial<IFieldsetIconPickerProps> = {}): IFieldsetIconPickerProps => ({
    fieldsetsCatalogLoading: false,
    onSelectFieldset: jest.fn(),
    ...overrides,
  });

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector: unknown) =>
      (selector as (s: unknown) => unknown)(EMPTY_STATE),
    );
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue([]);
  });

  it('fieldsetsCatalogLoading=true and empty catalog -> skeleton rows are rendered', () => {
    render(React.createElement(FieldsetIconPicker, makeProps({ fieldsetsCatalogLoading: true })));
    openPicker();

    expect(document.querySelectorAll('.dropdownlist-sm__skeleton')).toHaveLength(5);
  });

  it('fieldsetsCatalogLoading=false and empty catalog -> empty text is rendered', () => {
    render(React.createElement(FieldsetIconPicker, makeProps({ fieldsetsCatalogLoading: false })));
    openPicker();

    expect(screen.getByText(formatMsg('template.fieldset-picker.empty'))).toBeInTheDocument();
  });

  it('renders fieldsets sorted by order property ascending', () => {
    const catalogItems: IFieldsetCatalogItem[] = [
      makeCatalogItem(1, 'fs-a', 'Alpha', 2),
      makeCatalogItem(2, 'fs-b', 'Zeta', 0),
      makeCatalogItem(3, 'fs-c', 'Beta', 1),
    ];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(React.createElement(FieldsetIconPicker, makeProps()));
    openPicker();

    expect(getOptionTexts()).toEqual([
      expect.stringContaining('Zeta'),
      expect.stringContaining('Beta'),
      expect.stringContaining('Alpha'),
    ]);
  });

  it('click on fieldset option calls onSelectFieldset with fieldset object', () => {
    const onSelectFieldset = jest.fn();
    const catalogItems: IFieldsetCatalogItem[] = [makeCatalogItem(1, 'fs-1', 'My Fieldset', 0)];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(React.createElement(FieldsetIconPicker, makeProps({ onSelectFieldset })));
    openPicker();
    userEvent.click(screen.getByText('My Fieldset'));

    expect(onSelectFieldset).toHaveBeenCalledTimes(1);
    expect(onSelectFieldset).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
    expect(screen.queryByText('My Fieldset')).not.toBeInTheDocument();
  });

  it('background catalog load keeps the list when it is not empty', () => {
    const catalogItems: IFieldsetCatalogItem[] = [makeCatalogItem(1, 'fs-1', 'My Set', 0)];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(React.createElement(FieldsetIconPicker, makeProps({ fieldsetsCatalogLoading: true })));
    openPicker();

    expect(document.querySelectorAll('.dropdownlist-sm__skeleton')).toHaveLength(0);
    expect(screen.getByText('My Set')).toBeInTheDocument();
  });

  it('meta line displays fields and rules count using typed stub factories without as any', () => {
    const catalogItem = makeFieldsetCatalogItem({
      name: 'My Set',
      fields: [
        makeFieldsetField({ apiName: 'a' }),
        makeFieldsetField({ apiName: 'b' }),
        makeFieldsetField({ apiName: 'c' }),
      ],
      rules: [
        makeFieldsetTemplateRule(),
        makeFieldsetTemplateRule(),
        makeFieldsetTemplateRule(),
        makeFieldsetTemplateRule(),
        makeFieldsetTemplateRule(),
      ],
    });
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue([catalogItem]);

    render(React.createElement(FieldsetIconPicker, makeProps()));
    openPicker();

    expect(screen.getByText('3 fields · 5 rules')).toBeInTheDocument();
  });

  it('meta line displays "0 fields · 0 rules" when fields and rules are empty', () => {
    const catalogItem = makeFieldsetCatalogItem({
      name: 'My Set',
      fields: [],
      rules: [],
    });
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue([catalogItem]);

    render(React.createElement(FieldsetIconPicker, makeProps()));
    openPicker();

    expect(screen.getByText('0 fields · 0 rules')).toBeInTheDocument();
  });

  it('filters fieldsets by name typed into the search', () => {
    const catalogItems: IFieldsetCatalogItem[] = [
      makeCatalogItem(1, 'fs-search', 'Searchable Fieldset', 0),
      makeCatalogItem(2, 'fs-other', 'Other', 1),
    ];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(React.createElement(FieldsetIconPicker, makeProps()));
    openPicker();
    userEvent.type(screen.getByRole('textbox'), 'searchable');

    expect(getOptionTexts()).toEqual([expect.stringContaining('Searchable Fieldset')]);
  });
});
