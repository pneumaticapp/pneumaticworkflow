// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { DatasetRow } from '../DatasetRow';

import { validateDatasetRow } from '../../../../utils/validators';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('../../../UI/ModifyDropdown/ModifyDropdown', () => ({
  ModifyDropdown: jest.fn(() => null),
}));

jest.mock('../../../icons/CommentEditCancelIcon', () => ({
  CommentEditCancelIcon: () => null,
}));

jest.mock('../../../icons/CommentEditDoneIcon', () => ({
  CommentEditDoneIcon: () => null,
}));

jest.mock('../../../../utils/validators', () => ({
  validateDatasetRow: jest.fn(() => ''),
}));

describe('DatasetRow', () => {
  const mockOnSave = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnEdit = jest.fn();
  const mockOnCancel = jest.fn();

  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const SAVE_LABEL = formatMsg('datasets.row.save');
  const CANCEL_LABEL = formatMsg('datasets.row.cancel');

  const getSaveButton = () => screen.getByRole('button', { name: SAVE_LABEL });
  const getCancelButton = () => screen.getByRole('button', { name: CANCEL_LABEL });
  const getInput = () => screen.getByRole('textbox');

  const baseProps = {
    value: 'Apple',
    existingItems: ['Apple', 'Banana'],
    onSave: mockOnSave,
    onDelete: mockOnDelete,
    onEdit: mockOnEdit,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (validateDatasetRow as jest.Mock).mockReturnValue('');
  });

  it('displays value text when isEditing=false', () => {
    render(React.createElement(DatasetRow, baseProps));

    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('displays input with current value when isEditing=true', () => {
    render(React.createElement(DatasetRow, { ...baseProps, isEditing: true }));

    const input = getInput();
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('Apple');
  });

  it('calls onSave with trimmed value on Enter', () => {
    render(React.createElement(DatasetRow, { ...baseProps, isEditing: true, value: '' }));

    const input = getInput();
    userEvent.type(input, '  Cherry  ');
    userEvent.keyboard('{Enter}');

    expect(mockOnSave).toHaveBeenCalledTimes(1);
    expect(mockOnSave).toHaveBeenCalledWith('Cherry');
  });

  it('calls onCancel on Escape', () => {
    render(React.createElement(DatasetRow, { ...baseProps, isEditing: true }));

    userEvent.keyboard('{Escape}');

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('shows validation error and does not call onSave for duplicate value', () => {
    const ERROR_KEY = 'validation.dataset-row-exists';
    (validateDatasetRow as jest.Mock).mockReturnValue(ERROR_KEY);

    render(React.createElement(DatasetRow, { ...baseProps, isEditing: true, value: '' }));

    const input = getInput();
    userEvent.type(input, 'Banana');
    userEvent.keyboard('{Enter}');

    expect(validateDatasetRow).toHaveBeenCalledWith('Banana', ['Apple', 'Banana'], undefined);

    const expectedErrorText = formatMsg(ERROR_KEY);
    expect(screen.getByText(expectedErrorText)).toBeInTheDocument();

    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it('calls onSave when Save button is clicked', () => {
    render(React.createElement(DatasetRow, { ...baseProps, isEditing: true, value: '' }));

    const input = getInput();
    userEvent.type(input, 'Cherry');

    userEvent.click(getSaveButton());

    expect(mockOnSave).toHaveBeenCalledTimes(1);
    expect(mockOnSave).toHaveBeenCalledWith('Cherry');
  });

  it('calls onCancel when Cancel button is clicked', () => {
    render(React.createElement(DatasetRow, { ...baseProps, isEditing: true }));

    userEvent.click(getCancelButton());

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });
});
