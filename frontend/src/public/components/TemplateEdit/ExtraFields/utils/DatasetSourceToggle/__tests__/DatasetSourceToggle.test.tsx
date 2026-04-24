// <reference types="jest" />
import * as React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { DatasetSourceToggle } from '../DatasetSourceToggle';
import { DropdownList } from '../../../../../UI/DropdownList';
import { loadAllDatasets } from '../../../../../../redux/datasets/slice';
import { getEmptySelection } from '../../../../KickoffRedux/utils/getEmptySelection';
import { intlMock } from '../../../../../../__stubs__/intlMock';

jest.mock('../../../../../UI/DropdownList', () => ({
  DropdownList: jest.fn(() => null),
}));

jest.mock('react-outside-click-handler', () => ({
  __esModule: true,
  default: jest.fn(({ children }: any) =>
    React.createElement('div', { 'data-testid': 'outside-handler' }, children),
  ),
}));

jest.mock('../../../../KickoffRedux/utils/getEmptySelection', () => ({
  getEmptySelection: jest.fn(() => ({ id: 'empty', value: '', isSelected: false })),
}));

jest.mock('../../../../../../redux/datasets/slice', () => ({
  loadAllDatasets: jest.fn(() => ({ type: 'datasets/loadAllDatasets' })),
}));

jest.mock('react-responsive', () => ({
  useMediaQuery: () => false,
}));

jest.mock('../TruncatedTooltip', () => ({
  TruncatedTooltip: jest.fn(({ children }: any) => children),
}));

describe('DatasetSourceToggle', () => {
  const mockDispatch = jest.fn();
  const mockEditField = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const CUSTOM_TAB = formatMsg('template.field-source-custom');
  const DATASET_TAB = formatMsg('template.field-source-dataset');
  const CLEAR_LABEL = formatMsg('template.field-dataset-clear');

  const customField = {
    dataset: null,
    selections: [{ id: 's1', value: 'opt1', isSelected: true }],
  };

  const datasetField = {
    dataset: 5,
    selections: undefined,
  };

  const datasetsList = [
    { id: 5, name: 'My Dataset', description: '', dateCreatedTsp: 100, itemsCount: 3 },
    { id: 10, name: 'Other', description: '', dateCreatedTsp: 200, itemsCount: 0 },
  ];

  const defaultState = {
    datasets: {
      allDatasetsList: datasetsList,
      isAllDatasetsLoading: false,
      isAllDatasetsLoaded: true,
    },
  };

  const notLoadedState = {
    datasets: {
      allDatasetsList: [],
      isAllDatasetsLoading: false,
      isAllDatasetsLoaded: false,
    },
  };

  const baseProps = {
    field: customField as any,
    editField: mockEditField,
    isDisabled: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockImplementation((selector) => selector(defaultState));
  });

  it('shows children in Custom mode when field.dataset=null', () => {
    const childText = 'Custom Options Here';
    render(React.createElement(DatasetSourceToggle, baseProps,
      React.createElement('div', { 'data-testid': 'children' }, childText),
    ));

    expect(screen.getByTestId('children')).toBeInTheDocument();
    expect(screen.getByTestId('children')).toHaveTextContent(childText);
  });

  it('shows dataset name in Dataset mode when field.dataset=5', () => {
    render(React.createElement(DatasetSourceToggle, {
      ...baseProps,
      field: datasetField as any,
    }));

    expect(screen.queryByTestId('children')).not.toBeInTheDocument();
    expect(screen.getByText('My Dataset')).toBeInTheDocument();
  });

  it('calls editField with savedDataset when switching to Dataset tab', () => {
    render(React.createElement(DatasetSourceToggle, baseProps));

    userEvent.click(screen.getByText(DATASET_TAB));

    expect(mockEditField).toHaveBeenCalledTimes(1);
    expect(mockEditField).toHaveBeenCalledWith({
      dataset: null,
      selections: undefined,
    });
  });

  it('calls editField with emptySelection when switching to Custom tab', () => {
    render(React.createElement(DatasetSourceToggle, {
      ...baseProps,
      field: datasetField as any,
    }));

    userEvent.click(screen.getByText(CUSTOM_TAB));

    expect(mockEditField).toHaveBeenCalledTimes(1);
    expect(mockEditField).toHaveBeenCalledWith({
      dataset: null,
      selections: [getEmptySelection()],
    });
  });

  it('calls editField with dataset id when selecting from dropdown', () => {
    render(React.createElement(DatasetSourceToggle, baseProps));

    userEvent.click(screen.getByText(DATASET_TAB));
    mockEditField.mockClear();

    const dropdownMock = DropdownList as jest.Mock;
    const lastDropdownProps = dropdownMock.mock.calls[dropdownMock.mock.calls.length - 1][0];

    act(() => {
      lastDropdownProps.onChange({ label: 'My Dataset', value: '5' });
    });

    expect(mockEditField).toHaveBeenCalledTimes(1);
    expect(mockEditField).toHaveBeenCalledWith({ dataset: 5, selections: undefined });
  });

  it('does not render tabs when isDisabled=true', () => {
    render(React.createElement(DatasetSourceToggle, { ...baseProps, isDisabled: true }));

    expect(screen.queryByText(CUSTOM_TAB)).not.toBeInTheDocument();
    expect(screen.queryByText(DATASET_TAB)).not.toBeInTheDocument();
  });

  it('dispatches loadAllDatasets on mount when not loaded and not loading', () => {
    (useSelector as jest.Mock).mockImplementation((selector) => selector(notLoadedState));

    render(React.createElement(DatasetSourceToggle, baseProps));

    expect(mockDispatch).toHaveBeenCalledTimes(1);
    expect(mockDispatch).toHaveBeenCalledWith(loadAllDatasets());
  });

  it('calls editField with null dataset on Clear button click', () => {
    render(React.createElement(DatasetSourceToggle, {
      ...baseProps,
      field: datasetField as any,
    }));

    userEvent.click(screen.getByText(CLEAR_LABEL));

    expect(mockEditField).toHaveBeenCalledTimes(1);
    expect(mockEditField).toHaveBeenCalledWith({
      dataset: null,
      selections: [getEmptySelection()],
    });
  });
});
