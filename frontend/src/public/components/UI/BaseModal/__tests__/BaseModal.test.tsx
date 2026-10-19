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

  it('keeps the page locked when a closed modal mounts and unmounts under an open one', () => {
    jest.useFakeTimers();
    render(<BaseModal isOpen>outer</BaseModal>);

    const { unmount } = render(<BaseModal isOpen={false}>closed popup</BaseModal>);
    act(() => {
      jest.advanceTimersByTime(150);
    });
    expect(document.body.style.overflow).toBe('hidden');

    unmount();
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('keeps the page locked until the last open modal closes', () => {
    jest.useFakeTimers();
    const outer = render(<BaseModal isOpen>outer</BaseModal>);
    const inner = render(<BaseModal isOpen>inner</BaseModal>);

    inner.rerender(<BaseModal isOpen={false}>inner</BaseModal>);
    act(() => {
      jest.advanceTimersByTime(150);
    });
    expect(document.body.style.overflow).toBe('hidden');

    outer.rerender(<BaseModal isOpen={false}>outer</BaseModal>);
    act(() => {
      jest.advanceTimersByTime(150);
    });
    expect(document.body.style.overflow).toBe('');
  });
});
