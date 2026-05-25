// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { Datasets } from '../Datasets';
import { DatasetCard } from '../DatasetCard';
import { DatasetModal } from '../DatasetModal/DatasetModal';
import { AddCardButton } from '../../UI';
import { openCreateModal, loadDatasets } from '../../../redux/datasets/slice';
import { intlMock } from '../../../__stubs__/intlMock';
import { EDatasetsSorting } from '../../../types/dataset';

jest.mock('react-infinite-scroll-component', () => ({
  __esModule: true,
  default: jest.fn(({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'infinite-scroll' }, children),
  ),
}));

jest.mock('../../PageTitle', () => ({
  PageTitle: jest.fn(() => null),
}));

jest.mock('../../UI', () => ({
  AddCardButton: jest.fn(() => null),
}));

jest.mock('../../icons', () => ({
  AIPlusIcon: () => null,
}));

jest.mock('../DatasetCard', () => ({
  DatasetCard: jest.fn(() => null),
}));

jest.mock('../DatasetModal/DatasetModal', () => ({
  DatasetModal: jest.fn(() => null),
}));

jest.mock('../../../redux/datasets/slice', () => ({
  openCreateModal: jest.fn(() => ({ type: 'datasets/openCreateModal' })),
  loadDatasets: jest.fn((payload) => ({ type: 'datasets/loadDatasets', payload })),
}));

describe('Datasets', () => {
  const mockDispatch = jest.fn();

  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const NEW_DATASET_TITLE = formatMsg('datasets.new-dataset.title');

  const getAddCardButtonProps = () => {
    const mock = AddCardButton as unknown as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0];
  };

  const defaultMockState = {
    datasets: {
      datasetsList: { items: [], count: 0, offset: 0 },
      isLoading: false,
      sorting: EDatasetsSorting.DateDesc,
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockImplementation((selector) => selector(defaultMockState));
  });

  it('dispatches loadDatasets(0) on mount', () => {
    render(React.createElement(Datasets));

    expect(mockDispatch).toHaveBeenCalledWith(loadDatasets(0));
  });

  it('shows loading indicator when isLoading=true and list is empty', () => {
    const loadingState = {
      datasets: {
        ...defaultMockState.datasets,
        isLoading: true,
      },
    };
    (useSelector as jest.Mock).mockImplementation((selector) => selector(loadingState));

    const { container } = render(React.createElement(Datasets));

    expect(container.querySelector('.loading')).toBeInTheDocument();
  });

  it('renders DatasetCard for each dataset', () => {
    const datasets = [
      { id: 1, name: 'DS1', description: '', dateCreatedTsp: 100, itemsCount: 3 },
      { id: 2, name: 'DS2', description: '', dateCreatedTsp: 200, itemsCount: 5 },
    ];
    const stateWithData = {
      datasets: {
        ...defaultMockState.datasets,
        datasetsList: { items: datasets, count: 2, offset: 0 },
      },
    };
    (useSelector as jest.Mock).mockImplementation((selector) => selector(stateWithData));

    render(React.createElement(Datasets));

    const mock = DatasetCard as jest.Mock;
    expect(mock).toHaveBeenCalledTimes(2);
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ id: 1, name: 'DS1' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ id: 2, name: 'DS2' }), {});
  });

  it('dispatches openCreateModal when AddCardButton is clicked', () => {
    render(React.createElement(Datasets));

    const addCardProps = getAddCardButtonProps();
    expect(addCardProps.title).toBe(NEW_DATASET_TITLE);

    addCardProps.onClick();

    expect(mockDispatch).toHaveBeenCalledWith(openCreateModal());
  });

  it('renders DatasetModal for both Create and Edit', () => {
    render(React.createElement(Datasets));

    const mock = DatasetModal as jest.Mock;
    expect(mock).toHaveBeenCalledTimes(2);
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ type: 'create' }), {});
    expect(mock).toHaveBeenCalledWith(expect.objectContaining({ type: 'edit' }), {});
  });
});
