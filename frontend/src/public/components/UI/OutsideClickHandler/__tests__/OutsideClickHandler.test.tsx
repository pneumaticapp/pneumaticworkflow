import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import OutsideClickHandler from '../OutsideClickHandler';
import { IOutsideClickHandlerProperties } from '../types';

const renderComponent = (properties: Partial<IOutsideClickHandlerProperties> = {}) => {
  const onOutsideClick = properties.onOutsideClick || jest.fn();

  const renderResult = render(
    <div>
      <div data-testid="outside-element">Outside area</div>
      <OutsideClickHandler onOutsideClick={onOutsideClick} {...properties}>
        <button type="button">Inside button</button>
      </OutsideClickHandler>
    </div>,
  );

  return {
    ...renderResult,
    onOutsideClick,
    outsideElement: screen.getByTestId('outside-element'),
    insideButton: screen.getByRole('button', { name: 'Inside button' }),
  };
};

describe('OutsideClickHandler', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children elements', () => {
    renderComponent();

    expect(screen.getByRole('button', { name: 'Inside button' })).toBeInTheDocument();
  });

  it('applies custom display style when display is not block', () => {
    const { insideButton } = renderComponent({ display: 'inline-block' });

    expect(insideButton.parentElement).toHaveStyle({ display: 'inline-block' });
  });

  it('calls onOutsideClick when mousedown and mouseup occur outside', () => {
    const { outsideElement, onOutsideClick } = renderComponent();

    fireEvent.mouseDown(outsideElement);
    fireEvent.mouseUp(outsideElement);

    expect(onOutsideClick).toHaveBeenCalledTimes(1);
    expect(onOutsideClick).toHaveBeenCalledWith(expect.any(MouseEvent));
  });

  it('does not call onOutsideClick when mousedown and mouseup occur inside', () => {
    const { insideButton, onOutsideClick } = renderComponent();

    fireEvent.mouseDown(insideButton);
    fireEvent.mouseUp(insideButton);

    expect(onOutsideClick).not.toHaveBeenCalled();
  });

  it('does not call onOutsideClick when drag starts inside and ends outside', () => {
    const { insideButton, outsideElement, onOutsideClick } = renderComponent();

    fireEvent.mouseDown(insideButton);
    fireEvent.mouseUp(outsideElement);

    expect(onOutsideClick).not.toHaveBeenCalled();
  });

  it('does not call onOutsideClick when mousedown is outside and mouseup is inside', () => {
    const { insideButton, outsideElement, onOutsideClick } = renderComponent();

    fireEvent.mouseDown(outsideElement);
    fireEvent.mouseUp(insideButton);

    expect(onOutsideClick).not.toHaveBeenCalled();
  });

  it('does not call onOutsideClick on outside click when disabled is true', () => {
    const { outsideElement, onOutsideClick } = renderComponent({ disabled: true });

    fireEvent.mouseDown(outsideElement);
    fireEvent.mouseUp(outsideElement);

    expect(onOutsideClick).not.toHaveBeenCalled();
  });

  it('stops calling onOutsideClick when dynamically switched to disabled', () => {
    const onOutsideClick = jest.fn();
    const { outsideElement, rerender } = renderComponent({ disabled: false, onOutsideClick });

    fireEvent.mouseDown(outsideElement);
    fireEvent.mouseUp(outsideElement);
    expect(onOutsideClick).toHaveBeenCalledTimes(1);

    rerender(
      <div>
        <div data-testid="outside-element">Outside area</div>
        <OutsideClickHandler disabled={true} onOutsideClick={onOutsideClick}>
          <button type="button">Inside button</button>
        </OutsideClickHandler>
      </div>,
    );

    fireEvent.mouseDown(outsideElement);
    fireEvent.mouseUp(outsideElement);

    expect(onOutsideClick).toHaveBeenCalledTimes(1);
  });

  it('removes event listeners from document on unmount', () => {
    const { outsideElement, onOutsideClick, unmount } = renderComponent();

    unmount();

    fireEvent.mouseDown(outsideElement);
    fireEvent.mouseUp(outsideElement);

    expect(onOutsideClick).not.toHaveBeenCalled();
  });
});
