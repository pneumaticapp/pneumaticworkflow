import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { FieldsetModal } from '../FieldsetModal';
import { EFieldsetModalType } from '../types';

import {
  closeCreateModal,
  closeEditModal,
  createFieldsetAction,
  updateFieldsetAction,
} from '../../../../redux/fieldsets/slice';
import { validateFieldsetName } from '../../../../utils/validators';
import { intlMock } from '../../../../__stubs__/intlMock';
import { EFieldLabelPosition } from '../../../../types/fieldset';

jest.mock('../../../../redux/fieldsets/slice', () => ({
  closeCreateModal: jest.fn(() => ({ type: 'fieldsets/closeCreateModal' })),
  closeEditModal: jest.fn(() => ({ type: 'fieldsets/closeEditModal' })),
  createFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/createFieldsetAction', payload: p })),
  updateFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/updateFieldsetAction', payload: p })),
}));

jest.mock('../../../../utils/validators', () => ({
  validateFieldsetName: jest.fn(() => ''),
}));

jest.mock('../../../UI', () => ({
  Modal: jest.fn(({ isOpen, children }: { isOpen: boolean; children: React.ReactNode }) =>
    isOpen ? React.createElement('div', { 'data-testid': 'modal' }, children) : null,
  ),
  InputField: jest.fn(({ value, onChange, errorMessage }: {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    errorMessage?: string;
  }) =>
    React.createElement('div', null,
      React.createElement('input', {
        'data-testid': 'fieldset-name-input',
        value,
        onChange,
      }),
      errorMessage
        ? React.createElement('span', { 'data-testid': 'error-message' }, errorMessage)
        : null,
    ),
  ),
  Button: jest.fn(({ type, disabled, onClick, label }: {
    type?: string;
    disabled?: boolean;
    onClick?: () => void;
    label: string;
  }) =>
    React.createElement('button', {
      type: type || 'button',
      disabled,
      onClick,
      'data-testid': `btn-${label}`,
    }, label),
  ),
  Header: jest.fn(({ children }: { children: React.ReactNode }) =>
    React.createElement('span', null, children),
  ),
}));

describe('FieldsetModal', () => {
  const mockDispatch = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const CREATE_LABEL = formatMsg('fieldsets.modal-button-create');
  const CONFIRM_LABEL = formatMsg('fieldsets.modal-button-confirm');
  const CANCEL_LABEL = formatMsg('fieldsets.modal-button-cancel');

  const defaultState = {
    fieldsets: {
      isCreateModalOpen: false,
      isEditModalOpen: false,
      currentFieldset: null,
    },
  };

  const createOpenState = {
    fieldsets: {
      ...defaultState.fieldsets,
      isCreateModalOpen: true,
    },
  };

  const editOpenState = {
    fieldsets: {
      ...defaultState.fieldsets,
      isEditModalOpen: true,
      currentFieldset: {
        id: 10,
        name: 'Original Name',
        description: 'desc',
        labelPosition: EFieldLabelPosition.Top,
        layout: 'vertical' as const,
        order: 0,
        kickoffId: null,
        taskId: null,
        rules: [],
        fields: [],
        templateId: 5,
      },
    },
  };

  const getSubmitButton = (label: string) =>
    screen.getByTestId(`btn-${label}`);

  const getNameInput = () =>
    screen.getByTestId('fieldset-name-input');

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockImplementation((selector) => selector(defaultState));
    (validateFieldsetName as jest.Mock).mockReturnValue('');
  });

  describe('Create mode — submit', () => {
    it('dispatches createFieldsetAction on valid submit', () => {
      (useSelector as jest.Mock).mockImplementation((selector) => selector(createOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Create }));

      const input = getNameInput();
      userEvent.type(input, 'New FS');

      const submitBtn = getSubmitButton(CREATE_LABEL);
      userEvent.click(submitBtn);

      expect(mockDispatch).toHaveBeenCalledWith(
        createFieldsetAction({ name: 'New FS' }),
      );
      expect(mockDispatch).toHaveBeenCalledWith(closeCreateModal());
      expect(mockDispatch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Edit mode — submit and initialization', () => {
    it('dispatches updateFieldsetAction on changed name submit', () => {
      (useSelector as jest.Mock).mockImplementation((selector) => selector(editOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Edit }));

      const input = getNameInput();
      userEvent.clear(input);
      userEvent.type(input, 'New Name');

      const submitBtn = getSubmitButton(CONFIRM_LABEL);
      userEvent.click(submitBtn);

      expect(mockDispatch).toHaveBeenCalledWith(
        updateFieldsetAction({ id: 10, name: 'New Name' }),
      );
      expect(mockDispatch).toHaveBeenCalledWith(closeEditModal());
      expect(mockDispatch).toHaveBeenCalledTimes(2);
    });

    it('initializes input with currentFieldset name', () => {
      (useSelector as jest.Mock).mockImplementation((selector) => selector(editOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Edit }));

      const input = getNameInput();
      expect(input).toHaveValue('Original Name');
    });
  });

  describe('Validation', () => {
    it('shows error and does not dispatch action on invalid submit', () => {
      (validateFieldsetName as jest.Mock).mockReturnValue('Name is required');
      (useSelector as jest.Mock).mockImplementation((selector) => selector(createOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Create }));

      const input = getNameInput();
      userEvent.type(input, 'bad name');

      const submitBtn = getSubmitButton(CREATE_LABEL);
      userEvent.click(submitBtn);

      expect(screen.getByTestId('error-message')).toHaveTextContent('Name is required');
      expect(createFieldsetAction).not.toHaveBeenCalled();
      expect(updateFieldsetAction).not.toHaveBeenCalled();
    });

    it('updates inline error on input change after first submit', () => {
      (validateFieldsetName as jest.Mock).mockReturnValue('Name is required');
      (useSelector as jest.Mock).mockImplementation((selector) => selector(createOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Create }));

      const input = getNameInput();
      userEvent.type(input, 'bad name');

      const submitBtn = getSubmitButton(CREATE_LABEL);
      userEvent.click(submitBtn);

      (validateFieldsetName as jest.Mock).mockClear();
      (validateFieldsetName as jest.Mock).mockReturnValue('Still invalid');

      userEvent.type(input, 'a');

      expect(validateFieldsetName).toHaveBeenCalledTimes(1);
      expect(validateFieldsetName).toHaveBeenCalledWith('bad namea');
    });
  });

  describe('Submit button disabled state', () => {
    it('submit is disabled when Create input is empty', () => {
      (useSelector as jest.Mock).mockImplementation((selector) => selector(createOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Create }));

      const submitBtn = getSubmitButton(CREATE_LABEL);
      expect(submitBtn).toBeDisabled();
    });

    it('submit is disabled in Edit mode when input is unchanged', () => {
      (useSelector as jest.Mock).mockImplementation((selector) => selector(editOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Edit }));

      const submitBtn = getSubmitButton(CONFIRM_LABEL);
      expect(submitBtn).toBeDisabled();
    });

    it('submit is enabled in Edit mode after input change', () => {
      (useSelector as jest.Mock).mockImplementation((selector) => selector(editOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Edit }));

      const input = getNameInput();
      userEvent.type(input, ' updated');

      const submitBtn = getSubmitButton(CONFIRM_LABEL);
      expect(submitBtn).not.toBeDisabled();
    });
  });

  describe('Modal close', () => {
    it('dispatches closeCreateModal on Cancel click', () => {
      (useSelector as jest.Mock).mockImplementation((selector) => selector(createOpenState));

      render(React.createElement(FieldsetModal, { type: EFieldsetModalType.Create }));

      const cancelBtn = getSubmitButton(CANCEL_LABEL);
      userEvent.click(cancelBtn);

      expect(mockDispatch).toHaveBeenCalledWith(closeCreateModal());
      expect(mockDispatch).toHaveBeenCalledTimes(1);
    });
  });

  describe('State reset', () => {
    it('clears error when modal is reopened', () => {
      (validateFieldsetName as jest.Mock).mockReturnValue('Name is required');
      (useSelector as jest.Mock).mockImplementation((selector) => selector(createOpenState));

      const { rerender } = render(
        React.createElement(FieldsetModal, { type: EFieldsetModalType.Create }),
      );

      const input = getNameInput();
      userEvent.type(input, 'bad');

      const submitBtn = getSubmitButton(CREATE_LABEL);
      userEvent.click(submitBtn);

      expect(screen.getByTestId('error-message')).toBeInTheDocument();

      (useSelector as jest.Mock).mockImplementation((selector) => selector(defaultState));
      rerender(
        React.createElement(FieldsetModal, { type: EFieldsetModalType.Create }),
      );

      (validateFieldsetName as jest.Mock).mockReturnValue('');
      (useSelector as jest.Mock).mockImplementation((selector) => selector(createOpenState));
      rerender(
        React.createElement(FieldsetModal, { type: EFieldsetModalType.Create }),
      );

      expect(screen.queryByTestId('error-message')).not.toBeInTheDocument();
    });
  });
});
