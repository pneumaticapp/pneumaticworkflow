import * as React from 'react';
import { act, render } from '@testing-library/react';

import { BaseModal } from '../BaseModal';

describe('BaseModal', () => {
  afterEach(() => {
    jest.useRealTimers();
    document.body.style.overflow = '';
  });

  it('locks page scroll while open and releases it after closing', () => {
    jest.useFakeTimers();
    const { rerender } = render(<BaseModal isOpen>content</BaseModal>);

    expect(document.body.style.overflow).toBe('hidden');

    rerender(<BaseModal isOpen={false}>content</BaseModal>);
    act(() => {
      jest.advanceTimersByTime(150);
    });

    expect(document.body.style.overflow).toBe('');
  });

  it('releases page scroll when unmounted before the close animation ends', () => {
    jest.useFakeTimers();
    const { rerender, unmount } = render(<BaseModal isOpen>content</BaseModal>);

    rerender(<BaseModal isOpen={false}>content</BaseModal>);
    unmount();

    expect(document.body.style.overflow).toBe('');
  });
});
