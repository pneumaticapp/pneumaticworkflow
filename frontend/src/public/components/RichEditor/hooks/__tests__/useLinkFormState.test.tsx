import { createElement } from 'react';
import { render, screen, act } from '@testing-library/react';
import { useLinkFormState } from '../useLinkFormState';

if (typeof (global as unknown as { DOMRect?: unknown }).DOMRect === 'undefined') {
  (global as unknown as { DOMRect: new (x?: number, y?: number, w?: number, h?: number) => DOMRect }).DOMRect = class {
    left: number;
    top: number;
    width: number;
    height: number;
    right: number;
    bottom: number;
    x: number;
    y: number;
    constructor(x = 0, y = 0, w = 0, h = 0) {
      this.left = this.x = x;
      this.top = this.y = y;
      this.width = w;
      this.height = h;
      this.right = x + w;
      this.bottom = y + h;
    }
    toJSON(): unknown {
      return {};
    }
  } as unknown as new (x?: number, y?: number, w?: number, h?: number) => DOMRect;
}

function fakeRect(x: number, y: number, w: number, h: number): DOMRect {
  return new (global as unknown as { DOMRect: new (x: number, y: number, w: number, h: number) => DOMRect }).DOMRect(x, y, w, h);
}

function TestWrapper() {
  const { formState, openLinkForm, closeLinkForm } = useLinkFormState();
  return createElement(
    'div',
    null,
    createElement('span', { 'data-testid': 'is-open' }, String(formState.isOpen)),
    createElement('span', { 'data-testid': 'form-mode' }, formState.formMode),
    createElement('button', {
      type: 'button',
      onClick: () => openLinkForm(fakeRect(10, 10, 100, 20), 'create-link-at-selection', { current: null }),
    }, 'Open'),
    createElement('button', {
      type: 'button',
      onClick: () => openLinkForm(fakeRect(0, 0, 50, 20), 'create-link-from-scratch', { current: null }),
    }, 'Open from scratch'),
    createElement('button', { type: 'button', onClick: closeLinkForm }, 'Close'),
  );
}

describe('useLinkFormState', () => {
  it('starts with form closed', () => {
    render(createElement(TestWrapper, null));
    expect(screen.getByTestId('is-open')).toHaveTextContent('false');
  });

  it('opens form with create-link-at-selection mode', () => {
    render(createElement(TestWrapper, null));
    act(() => {
      screen.getByText('Open').click();
    });
    expect(screen.getByTestId('is-open')).toHaveTextContent('true');
    expect(screen.getByTestId('form-mode')).toHaveTextContent('create-link-at-selection');
  });

  it('opens form with create-link-from-scratch mode', () => {
    render(createElement(TestWrapper, null));
    act(() => {
      screen.getByText('Open from scratch').click();
    });
    expect(screen.getByTestId('is-open')).toHaveTextContent('true');
    expect(screen.getByTestId('form-mode')).toHaveTextContent('create-link-from-scratch');
  });

  it('closes form when closeLinkForm is called', () => {
    render(createElement(TestWrapper, null));
    act(() => {
      screen.getByText('Open').click();
    });
    expect(screen.getByTestId('is-open')).toHaveTextContent('true');
    act(() => {
      screen.getByText('Close').click();
    });
    expect(screen.getByTestId('is-open')).toHaveTextContent('false');
  });
});
