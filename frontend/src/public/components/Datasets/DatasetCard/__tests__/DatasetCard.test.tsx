// <reference types="jest" />
import * as React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { DatasetCard } from '../DatasetCard';
import { Dropdown } from '../../../UI';
import { WarningPopup } from '../../../UI/WarningPopup';
import { history } from '../../../../utils/history';
import {
  openEditModal,
  deleteDatasetAction,
  setCurrentDataset,
  cloneDatasetAction,
} from '../../../../redux/datasets/slice';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('../../../../redux/datasets/slice', () => ({
  openEditModal: jest.fn(() => ({ type: 'datasets/openEditModal' })),
  deleteDatasetAction: jest.fn((payload) => ({ type: 'datasets/deleteDatasetAction', payload })),
  setCurrentDataset: jest.fn((payload) => ({ type: 'datasets/setCurrentDataset', payload })),
  cloneDatasetAction: jest.fn((payload) => ({ type: 'datasets/cloneDatasetAction', payload })),
}));

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../../utils/strings', () => ({
  sanitizeText: jest.fn((text: string) => text),
}));

jest.mock('../../../../utils/dateTime', () => ({
  formatDateTimeAmPm: jest.fn(() => 'Jan 1, 2026 12:00 AM'),
}));

jest.mock('../../../UI', () => ({
  Dropdown: jest.fn(() => null),
}));

jest.mock('../../../UI/WarningPopup', () => ({
  WarningPopup: jest.fn(() => null),
}));

jest.mock('../../../icons', () => ({
  MoreIcon: () => null,
  PencilIcon: () => null,
  TrashIcon: () => null,
  UnionIcon: () => null,
}));

describe('DatasetCard', () => {
  const mockDispatch = jest.fn();

  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const EDIT_LABEL = formatMsg('datasets.edit');
  const CLONE_LABEL = formatMsg('datasets.clone');
  const DELETE_LABEL = formatMsg('datasets.delete');

  const baseProps = {
    id: 42,
    name: 'My Dataset',
    description: 'Test description',
    dateCreatedTsp: 1704067200,
    itemsCount: 5,
  };

  const getDropdownOptions = () => {
    const mock = Dropdown as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0].options;
  };

  const findOption = (label: string) => {
    const options = getDropdownOptions();
    return options.find((opt: { label: string }) => opt.label === label);
  };

  const getWarningPopupProps = () => {
    const mock = WarningPopup as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0];
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  it('renders the dataset name', () => {
    render(React.createElement(DatasetCard, baseProps));
    expect(screen.getByRole('link')).toHaveTextContent('My Dataset');
  });

  it('hides footer when itemsCount is 0', () => {
    render(React.createElement(DatasetCard, { ...baseProps, itemsCount: 0 }));
    expect(screen.queryByText(/Jan 1, 2026/)).not.toBeInTheDocument();
  });

  it('shows footer with entries and date when itemsCount > 0', () => {
    render(React.createElement(DatasetCard, baseProps));
    expect(screen.getByText(/Jan 1, 2026/)).toBeInTheDocument();
  });

  it('navigates to dataset detail on title click', () => {
    render(React.createElement(DatasetCard, baseProps));
    userEvent.click(screen.getByRole('link'));
    expect(history.push).toHaveBeenCalledWith('/datasets/42/');
  });

  it('dispatches setCurrentDataset and openEditModal on Edit option click', () => {
    render(React.createElement(DatasetCard, baseProps));
    findOption(EDIT_LABEL).onClick();

    expect(mockDispatch).toHaveBeenCalledWith(setCurrentDataset({
      id: 42,
      name: 'My Dataset',
      description: 'Test description',
      dateCreatedTsp: 1704067200,
      items: [],
    }));
    expect(mockDispatch).toHaveBeenCalledWith(openEditModal());
  });

  it('dispatches cloneDatasetAction on Clone option click', () => {
    render(React.createElement(DatasetCard, baseProps));
    findOption(CLONE_LABEL).onClick();

    expect(mockDispatch).toHaveBeenCalledWith(cloneDatasetAction({ id: 42 }));
  });

  it('opens WarningPopup on Delete click, then dispatches deleteDatasetAction on confirm', () => {
    render(React.createElement(DatasetCard, baseProps));

    let popupProps = getWarningPopupProps();
    expect(popupProps.isOpen).toBe(false);

    act(() => {
      findOption(DELETE_LABEL).onClick();
    });

    popupProps = getWarningPopupProps();
    expect(popupProps.isOpen).toBe(true);

    act(() => {
      popupProps.onConfirm();
    });
    expect(mockDispatch).toHaveBeenCalledWith(deleteDatasetAction({ id: 42 }));
  });
});
