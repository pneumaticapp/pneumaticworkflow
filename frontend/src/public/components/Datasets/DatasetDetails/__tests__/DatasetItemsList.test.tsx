// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';

import { DatasetItemsList } from '../DatasetItemsList';
import { DatasetRow } from '../../DatasetRow/DatasetRow';
import { Placeholder, SelectMenu, InputField } from '../../../UI';
import { intlMock } from '../../../../__stubs__/intlMock';
import { EDatasetsSorting } from '../../../../types/dataset';

jest.mock('../../DatasetRow/DatasetRow', () => ({
  DatasetRow: jest.fn(() => null),
}));

jest.mock('../../../UI', () => ({
  Placeholder: jest.fn(() => null),
  SelectMenu: jest.fn(() => null),
  InputField: jest.fn(() => null),
}));

jest.mock('../../../icons', () => ({
  SearchMediumIcon: () => null,
}));

jest.mock('../../../Tasks/TasksPlaceholderIcon', () => ({
  TasksPlaceholderIcon: () => null,
}));

jest.mock('react-responsive', () => ({
  useMediaQuery: () => false,
}));

describe('DatasetItemsList', () => {
  const mockOnSearchChange = jest.fn();
  const mockOnSortingChange = jest.fn();
  const mockOnSaveNewRow = jest.fn();
  const mockOnCancelNewRow = jest.fn();
  const mockOnStartEdit = jest.fn();
  const mockOnEditRow = jest.fn();
  const mockOnCancelEdit = jest.fn();
  const mockOnDeleteRow = jest.fn();

  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const EMPTY_TITLE = formatMsg('datasets.empty-list.title');

  const baseProps = {
    sortedItems: [] as any[],
    allItemValues: [] as string[],
    isAddingRow: false,
    editingItemId: null,
    searchText: '',
    sorting: EDatasetsSorting.DateDesc,
    onSearchChange: mockOnSearchChange,
    onSortingChange: mockOnSortingChange,
    onSaveNewRow: mockOnSaveNewRow,
    onCancelNewRow: mockOnCancelNewRow,
    onStartEdit: mockOnStartEdit,
    onEditRow: mockOnEditRow,
    onCancelEdit: mockOnCancelEdit,
    onDeleteRow: mockOnDeleteRow,
  };

  const getPlaceholderProps = () => {
    const mock = Placeholder as jest.Mock;
    if (!mock.mock.calls.length) return null;
    return mock.mock.calls[mock.mock.calls.length - 1][0];
  };

  const getDatasetRowCalls = () => (DatasetRow as unknown as jest.Mock).mock.calls;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows Placeholder when list is empty with no adding and no search', () => {
    render(React.createElement(DatasetItemsList, baseProps));

    const placeholderProps = getPlaceholderProps();
    expect(placeholderProps).not.toBeNull();
    expect(placeholderProps.title).toBe(EMPTY_TITLE);
  });

  it('renders DatasetRow for each item', () => {
    const items = [
      { id: 1, value: 'Apple', order: 0 },
      { id: 2, value: 'Banana', order: 1 },
    ];

    render(React.createElement(DatasetItemsList, { ...baseProps, sortedItems: items }));

    expect(getPlaceholderProps()).toBeNull();

    const calls = getDatasetRowCalls();
    expect(calls).toHaveLength(2);
    expect(calls[0][0]).toEqual(expect.objectContaining({ value: 'Apple' }));
    expect(calls[1][0]).toEqual(expect.objectContaining({ value: 'Banana' }));
  });

  it('renders an additional DatasetRow with isEditing when isAddingRow=true', () => {
    render(React.createElement(DatasetItemsList, { ...baseProps, isAddingRow: true }));

    const calls = getDatasetRowCalls();
    expect(calls).toHaveLength(1);
    expect(calls[0][0]).toEqual(expect.objectContaining({ isEditing: true }));
  });

  it('renders InputField for search and SelectMenu for sorting', () => {
    render(React.createElement(DatasetItemsList, baseProps));

    expect(InputField as jest.Mock).toHaveBeenCalledTimes(1);
    expect(SelectMenu as jest.Mock).toHaveBeenCalledTimes(1);
    expect(SelectMenu as jest.Mock).toHaveBeenCalledWith(
      expect.objectContaining({ activeValue: EDatasetsSorting.DateDesc }),
      {},
    );
  });
});
