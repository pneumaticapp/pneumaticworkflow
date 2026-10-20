import * as React from 'react';
import { useRef } from 'react';
import { act, render } from '@testing-library/react';

import { useHashLink } from '../useHashLink';
import { history } from '../../utils/history';

function HashLinkTarget({ hash, handle }: { hash: string; handle?(): void }) {
  const element = useRef<HTMLDivElement | null>(null);
  useHashLink([{ hash, element, handle }]);

  return <div ref={element} />;
}

describe('useHashLink', () => {
  const scrollIntoView = jest.fn();

  beforeEach(() => {
    scrollIntoView.mockClear();
    Element.prototype.scrollIntoView = scrollIntoView;
    history.replace('/templates/1');
  });

  it('expands and scrolls to the section matching the hash on mount', () => {
    const handle = jest.fn();
    history.replace('/templates/1#zapier');

    render(<HashLinkTarget hash="zapier" handle={handle} />);

    expect(handle).toHaveBeenCalledTimes(1);
    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'nearest' });
  });

  it('scrolls when the hash changes after mount', () => {
    render(<HashLinkTarget hash="api" />);
    expect(scrollIntoView).not.toHaveBeenCalled();

    act(() => {
      history.push('/templates/1#api');
    });

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'nearest' });
  });

  it('ignores hashes that belong to other sections', () => {
    history.replace('/templates/1#webhook');

    render(<HashLinkTarget hash="api" />);

    expect(scrollIntoView).not.toHaveBeenCalled();
  });
});
