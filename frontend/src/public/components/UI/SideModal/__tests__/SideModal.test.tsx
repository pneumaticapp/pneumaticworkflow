import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { SideModal } from '../SideModal';

jest.mock('../../../icons', () => ({ ClearIcon: () => null }));
jest.mock('../../../../utils/history', () => ({ history: { listen: jest.fn() } }));

describe('SideModal', () => {
  const CLOSE_BUTTON_NAME = 'Close modal';
  const CHILDREN_TEXT = 'Modal content';
  const onClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the modal in document.body instead of the render container', () => {
    const { container } = render(<SideModal onClose={onClose} />);

    expect(container).toBeEmptyDOMElement();
    expect(screen.getByRole('button', { name: CLOSE_BUTTON_NAME })).toBeInTheDocument();
  });

  it('calls onClose once when the close button is clicked', () => {
    render(<SideModal onClose={onClose} />);

    userEvent.click(screen.getByRole('button', { name: CLOSE_BUTTON_NAME }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('renders children inside the modal', () => {
    render(<SideModal onClose={onClose}>{CHILDREN_TEXT}</SideModal>);

    expect(screen.getByText(CHILDREN_TEXT)).toBeInTheDocument();
  });

  it('is opened by default', () => {
    render(<SideModal onClose={onClose} />);

    expect(screen.getByTestId('side-modal')).toHaveClass('side-modal_opened');
  });

  it('calls onClose once when clicking outside the modal', () => {
    render(<SideModal onClose={onClose} />);

    userEvent.click(document.body);

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
