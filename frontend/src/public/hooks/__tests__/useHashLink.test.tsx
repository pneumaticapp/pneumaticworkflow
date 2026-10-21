import * as React from 'react';
import { useRef, useState } from 'react';
import { act, render } from '@testing-library/react';

import { useHashLink } from '../useHashLink';
import { history } from '../../utils/history';

function HashLinkTarget({ hash }: { hash: string }) {
  const element = useRef<HTMLDivElement | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  useHashLink([{ hash, element, handle: () => setIsExpanded(true) }]);

  return <div ref={element}>{isExpanded && <div data-testid="expanded-content" />}</div>;
}

describe('useHashLink', () => {
  const scrollIntoView = jest.fn();
  let wasExpandedOnScroll: boolean[];

  beforeEach(() => {
    jest.useFakeTimers();
    wasExpandedOnScroll = [];
    scrollIntoView.mockReset();
    scrollIntoView.mockImplementation(function recordExpansion(this: HTMLElement) {
      wasExpandedOnScroll.push(Boolean(this.querySelector('[data-testid="expanded-content"]')));
    });
    Element.prototype.scrollIntoView = scrollIntoView;
    history.replace('/templates/1');
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const flushFrame = () =>
    act(() => {
      jest.runOnlyPendingTimers();
    });

  it('scrolls to the section matching the hash on mount after it expands', () => {
    history.replace('/templates/1#zapier');

    render(<HashLinkTarget hash="zapier" />);
    expect(scrollIntoView).not.toHaveBeenCalled();
    flushFrame();

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });
    expect(wasExpandedOnScroll).toEqual([true]);
  });

  it('scrolls to the expanded section when the hash changes after mount', () => {
    render(<HashLinkTarget hash="api" />);

    act(() => {
      history.push('/templates/1#api');
    });
    flushFrame();

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });
    expect(wasExpandedOnScroll).toEqual([true]);
  });

  it('ignores hashes that belong to other sections', () => {
    history.replace('/templates/1#webhook');

    render(<HashLinkTarget hash="api" />);
    flushFrame();

    expect(scrollIntoView).not.toHaveBeenCalled();
  });
});
