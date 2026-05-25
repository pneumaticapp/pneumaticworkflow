// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { DatasetModal } from '../DatasetModal';
import { EDatasetModalType } from '../types';
import {
  closeCreateModal,
  createDatasetAction,
  updateDatasetAction,
} from '../../../../redux/datasets/slice';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('../../../../redux/datasets/slice', () => ({
  closeCreateModal: jest.fn(() => ({ type: 'datasets/closeCreateModal' })),
  closeEditModal: jest.fn(() => ({ type: 'datasets/closeEditModal' })),
  createDatasetAction: jest.fn((payload) => ({ type: 'datasets/createDatasetAction', payload })),
  updateDatasetAction: jest.fn((payload) => ({ type: 'datasets/updateDatasetAction', payload })),
}));

jest.mock('../../../../utils/validators', () => {
  const actual = jest.requireActual('../../../../utils/validators');
  return { ...actual };
});

jest.mock('../../../UI', () => ({
  Modal: jest.fn(({ isOpen, children }: { isOpen: boolean; children: React.ReactNode }) =>
    isOpen ? React.createElement('div', { 'data-testid': 'modal' }, children) : null,
  ),
  Button: jest.fn((props: { label: string; disabled?: boolean; type?: string; onClick?: () => void }) =>
    React.createElement('button', {
      type: props.type || 'button',
      disabled: props.disabled,
      onClick: props.onClick,
    }, props.label),
  ),
  InputField: jest.fn((props: { value: string; onChange: (e: any) => void; errorMessage?: string }) =>
    React.createElement('div', null,
      React.createElement('input', {
        'data-testid': 'name-input',
        value: props.value,
        onChange: props.onChange,
      }),
      props.errorMessage && React.createElement('span', { 'data-testid': 'error' }, props.errorMessage),
    ),
  ),
  Header: jest.fn(({ children }: { children: React.ReactNode }) =>
    React.createElement('h2', { 'data-testid': 'modal-title' }, children),
  ),
}));

describe('DatasetModal', () => {
  const mockDispatch = jest.fn();

  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const CREATE_LABEL = formatMsg('datasets.modal-button-create');
  const CONFIRM_LABEL = formatMsg('datasets.modal-button-confirm');
  const CANCEL_LABEL = formatMsg('datasets.modal-button-cancel');

  const setupCreateMode = () => {
    (useSelector as jest.Mock).mockImplementation((selector: Function) =>
      selector({
        datasets: {
          isCreateModalOpen: true,
          isEditModalOpen: false,
          currentDataset: null,
        },
      }),
    );
  };

  const setupEditMode = (name = 'Existing DS') => {
    const mockState = {
      datasets: {
        isCreateModalOpen: false,
        isEditModalOpen: true,
        currentDataset: { id: 10, name, description: '', dateCreatedTsp: 0, items: [] },
      },
    };
    (useSelector as jest.Mock).mockImplementation((selector: Function) =>
      selector(mockState),
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  it('renders Create modal with title', () => {
    setupCreateMode();
    render(React.createElement(DatasetModal, { type: EDatasetModalType.Create }));
    expect(screen.getByTestId('modal-title')).toBeInTheDocument();
  });

  it('renders Edit modal with title', () => {
    setupEditMode();
    render(React.createElement(DatasetModal, { type: EDatasetModalType.Edit }));
    expect(screen.getByTestId('modal-title')).toBeInTheDocument();
  });

  it('initializes input value from currentDataset.name in Edit mode', () => {
    setupEditMode('My Dataset');
    render(React.createElement(DatasetModal, { type: EDatasetModalType.Edit }));
    const input = screen.getByTestId('name-input') as HTMLInputElement;
    expect(input.value).toBe('My Dataset');
  });

  it('dispatches createDatasetAction on Create submit', () => {
    setupCreateMode();
    render(React.createElement(DatasetModal, { type: EDatasetModalType.Create }));

    userEvent.type(screen.getByTestId('name-input'), 'New Dataset');

    const submitBtn = screen.getByRole('button', { name: CREATE_LABEL });
    userEvent.click(submitBtn);

    expect(mockDispatch).toHaveBeenCalledWith(createDatasetAction({ name: 'New Dataset' }));
  });

  it('dispatches updateDatasetAction on Edit submit', () => {
    setupEditMode('Old Name');
    render(React.createElement(DatasetModal, { type: EDatasetModalType.Edit }));

    userEvent.type(screen.getByTestId('name-input'), ' v2');

    const submitBtn = screen.getByRole('button', { name: CONFIRM_LABEL });
    userEvent.click(submitBtn);

    expect(mockDispatch).toHaveBeenCalledWith(updateDatasetAction({ id: 10, name: 'Old Name v2' }));
  });

  it('disables submit button when name is empty', () => {
    setupCreateMode();
    render(React.createElement(DatasetModal, { type: EDatasetModalType.Create }));

    const submitBtn = screen.getByRole('button', { name: CREATE_LABEL });
    expect(submitBtn).toBeDisabled();
  });

  it('dispatches closeCreateModal on Cancel click', () => {
    setupCreateMode();
    render(React.createElement(DatasetModal, { type: EDatasetModalType.Create }));

    const cancelBtn = screen.getByRole('button', { name: CANCEL_LABEL });
    userEvent.click(cancelBtn);

    expect(mockDispatch).toHaveBeenCalledWith(closeCreateModal());
  });
});
