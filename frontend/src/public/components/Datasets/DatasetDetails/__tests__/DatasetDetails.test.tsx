// <reference types="jest" />
import * as React from 'react';
import { render, act } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import DatasetDetails from '../DatasetDetails';
import { DatasetItemsList } from '../DatasetItemsList';
import { Button } from '../../../UI';
import { history } from '../../../../utils/history';
import {
  loadCurrentDataset,
  resetCurrentDataset,
  updateDatasetAction,
} from '../../../../redux/datasets/slice';
import { getSortedAndFilteredDatasetItems } from '../../../../utils/dataset';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../../utils/dataset', () => ({
  getSortedAndFilteredDatasetItems: jest.fn(() => []),
}));

jest.mock('../../../../redux/datasets/slice', () => ({
  openEditModal: jest.fn(() => ({ type: 'datasets/openEditModal' })),
  cloneDatasetAction: jest.fn((p) => ({ type: 'datasets/cloneDatasetAction', payload: p })),
  deleteDatasetAction: jest.fn((p) => ({ type: 'datasets/deleteDatasetAction', payload: p })),
  updateDatasetAction: jest.fn((p) => ({ type: 'datasets/updateDatasetAction', payload: p })),
  loadCurrentDataset: jest.fn((p) => ({ type: 'datasets/loadCurrentDataset', payload: p })),
  resetCurrentDataset: jest.fn(() => ({ type: 'datasets/resetCurrentDataset' })),
}));

jest.mock('../../../UI', () => ({
  ModifyDropdown: jest.fn(() => null),
  Button: jest.fn(() => null),
}));

jest.mock('../../../icons', () => ({
  BoldPlusIcon: () => null,
}));

jest.mock('../../DatasetModal/DatasetModal', () => ({
  DatasetModal: jest.fn(() => null),
}));

jest.mock('../DatasetDetailsSkeleton', () => ({
  DatasetDetailsSkeleton: jest.fn(() =>
    React.createElement('div', { 'data-testid': 'skeleton' }),
  ),
}));

jest.mock('../DatasetItemsList', () => ({
  DatasetItemsList: jest.fn(() => null),
}));

jest.mock('react-responsive', () => ({
  useMediaQuery: () => false,
}));

describe('DatasetDetails', () => {
  const mockDispatch = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const ADD_ROW_LABEL = formatMsg('datasets.add-row');

  const makeProps = (id: string = '42') => ({
    match: { params: { id }, isExact: true, path: '', url: '' },
    location: { pathname: `/datasets/${id}/`, search: '', hash: '', state: undefined },
    history: history as any,
  });

  const getButtonProps = () => {
    const mock = Button as unknown as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0];
  };

  const getItemsListProps = () => {
    const mock = DatasetItemsList as jest.Mock;
    if (!mock.mock.calls.length) return null;
    return mock.mock.calls[mock.mock.calls.length - 1][0];
  };

  const mockDataset = {
    id: 42,
    name: 'Test Dataset',
    description: '',
    dateCreatedTsp: 100,
    items: [
      { id: 1, value: 'Apple', order: 0 },
      { id: 2, value: 'Banana', order: 1 },
    ],
  };

  const loadedState = {
    datasets: {
      currentDataset: mockDataset,
      isCurrentDatasetLoading: false,
    },
  };

  const loadingState = {
    datasets: {
      currentDataset: null,
      isCurrentDatasetLoading: true,
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockImplementation((selector) => selector(loadedState));
    (getSortedAndFilteredDatasetItems as jest.Mock).mockReturnValue(mockDataset.items);
  });

  it('dispatches loadCurrentDataset({ id }) on mount with valid id', () => {
    const noDatasetState = {
      datasets: {
        currentDataset: null,
        isCurrentDatasetLoading: true,
      },
    };
    (useSelector as jest.Mock).mockImplementation((selector) => selector(noDatasetState));

    render(React.createElement(DatasetDetails, makeProps('42')));

    expect(mockDispatch).toHaveBeenCalledWith(loadCurrentDataset({ id: 42 }));
  });

  it('redirects to /datasets/ when id is NaN', () => {
    render(React.createElement(DatasetDetails, makeProps('abc')));

    expect(history.push).toHaveBeenCalledTimes(1);
    expect(history.push).toHaveBeenCalledWith('/datasets/');
  });

  it('renders DatasetDetailsSkeleton when isLoading=true', () => {
    (useSelector as jest.Mock).mockImplementation((selector) => selector(loadingState));

    const { getByTestId } = render(React.createElement(DatasetDetails, makeProps()));

    expect(getByTestId('skeleton')).toBeInTheDocument();
  });

  it('renders h1 with dataset name when loaded', () => {
    const { getByRole } = render(React.createElement(DatasetDetails, makeProps()));

    const heading = getByRole('heading', { level: 1 });
    expect(heading).toHaveTextContent('Test Dataset');
  });

  it('passes isAddingRow=true to DatasetItemsList after clicking Add Row button', () => {
    render(React.createElement(DatasetDetails, makeProps()));

    const buttonProps = getButtonProps();
    expect(buttonProps.label).toBe(ADD_ROW_LABEL);

    expect(getItemsListProps().isAddingRow).toBe(false);

    act(() => {
      buttonProps.onClick();
    });

    expect(getItemsListProps().isAddingRow).toBe(true);
  });

  it('dispatches updateDatasetAction with new item on handleSaveNewRow', () => {
    render(React.createElement(DatasetDetails, makeProps()));

    const onSaveNewRow = getItemsListProps().onSaveNewRow;
    act(() => {
      onSaveNewRow('Cherry');
    });

    expect(mockDispatch).toHaveBeenCalledWith(updateDatasetAction({
      id: 42,
      items: [
        { id: 1, value: 'Apple', order: 0 },
        { id: 2, value: 'Banana', order: 1 },
        { value: 'Cherry', order: 2 },
      ],
    }));
  });

  it('dispatches updateDatasetAction with filtered items on handleDeleteRow', () => {
    render(React.createElement(DatasetDetails, makeProps()));

    const onDeleteRow = getItemsListProps().onDeleteRow;
    act(() => {
      onDeleteRow(1);
    });

    expect(mockDispatch).toHaveBeenCalledWith(updateDatasetAction({
      id: 42,
      items: [
        { id: 2, value: 'Banana', order: 1 },
      ],
    }));
  });

  it('dispatches resetCurrentDataset on unmount', () => {
    const { unmount } = render(React.createElement(DatasetDetails, makeProps()));

    mockDispatch.mockClear();
    unmount();

    expect(mockDispatch).toHaveBeenCalledTimes(1);
    expect(mockDispatch).toHaveBeenCalledWith(resetCurrentDataset());
  });
});
