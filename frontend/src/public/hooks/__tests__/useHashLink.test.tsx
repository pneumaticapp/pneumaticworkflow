import * as React from 'react';
import { render, cleanup } from '@testing-library/react';

import { useHashLink } from '../useHashLink';
import { scrollToElementWhenStable } from '../../utils/scroll';
import { history } from '../../utils/history';

jest.mock('../../utils/scroll', () => ({
  scrollToElementWhenStable: jest.fn(),
}));

const scrollToElementWhenStableMock = scrollToElementWhenStable as jest.Mock;

type TProbeProps = {
  handleApi?(): void;
  handleShare?(): void;
};

function Probe({ handleApi, handleShare }: TProbeProps) {
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  useHashLink([
    { element: containerRef, hash: 'api', handle: handleApi },
    { element: containerRef, hash: 'share', handle: handleShare },
  ]);

  return <div ref={containerRef} data-testid="section" />;
}

describe('useHashLink', () => {
  let cancel: jest.Mock;

  beforeEach(() => {
    cancel = jest.fn();
    scrollToElementWhenStableMock.mockReset();
    scrollToElementWhenStableMock.mockReturnValue(cancel);
    history.replace('/templates/1');
  });

  afterEach(cleanup);

  it('expands the matching section and scrolls to it on mount', () => {
    history.replace('/templates/1#api');
    const handleApi = jest.fn();

    const { getByTestId } = render(<Probe handleApi={handleApi} />);

    expect(handleApi).toHaveBeenCalledTimes(1);
    expect(scrollToElementWhenStableMock).toHaveBeenCalledWith(getByTestId('section'));
  });

  it('does nothing without a hash', () => {
    const handleApi = jest.fn();

    render(<Probe handleApi={handleApi} />);

    expect(handleApi).not.toHaveBeenCalled();
    expect(scrollToElementWhenStableMock).not.toHaveBeenCalled();
  });

  it('ignores a hash it does not own', () => {
    history.replace('/templates/1#zapier');
    const handleApi = jest.fn();

    render(<Probe handleApi={handleApi} />);

    expect(handleApi).not.toHaveBeenCalled();
    expect(scrollToElementWhenStableMock).not.toHaveBeenCalled();
  });

  it('reacts to a hash pushed while the page is already open', () => {
    const handleApi = jest.fn();
    render(<Probe handleApi={handleApi} />);

    history.push('/templates/1#api');

    expect(handleApi).toHaveBeenCalledTimes(1);
    expect(scrollToElementWhenStableMock).toHaveBeenCalledTimes(1);
  });

  it('cancels the pending scroll before starting a new one', () => {
    const handleApi = jest.fn();
    const handleShare = jest.fn();
    render(<Probe handleApi={handleApi} handleShare={handleShare} />);

    history.push('/templates/1#api');
    history.push('/templates/1#share');

    expect(cancel).toHaveBeenCalledTimes(1);
    expect(handleShare).toHaveBeenCalledTimes(1);
    expect(scrollToElementWhenStableMock).toHaveBeenCalledTimes(2);
  });

  it('cancels the pending scroll when navigating to a hash it does not own', () => {
    render(<Probe handleApi={jest.fn()} />);
    history.push('/templates/1#api');

    history.push('/templates/1#zap-manager');

    expect(cancel).toHaveBeenCalledTimes(1);
    expect(scrollToElementWhenStableMock).toHaveBeenCalledTimes(1);
  });

  it('cancels the pending scroll when navigating away from the hash entirely', () => {
    render(<Probe handleApi={jest.fn()} />);
    history.push('/templates/1#api');

    history.push('/templates/1');

    expect(cancel).toHaveBeenCalledTimes(1);
    expect(scrollToElementWhenStableMock).toHaveBeenCalledTimes(1);
  });

  it('does not re-cancel an already superseded scroll', () => {
    render(<Probe handleApi={jest.fn()} />);
    history.push('/templates/1#api');

    history.push('/templates/1');
    history.push('/templates/1?a=1');

    expect(cancel).toHaveBeenCalledTimes(1);
  });

  it('cancels the pending scroll and stops listening on unmount', () => {
    history.replace('/templates/1#api');
    const { unmount } = render(<Probe handleApi={jest.fn()} />);

    unmount();
    scrollToElementWhenStableMock.mockClear();
    history.push('/templates/1#share');

    expect(cancel).toHaveBeenCalledTimes(1);
    expect(scrollToElementWhenStableMock).not.toHaveBeenCalled();
  });

  it('uses the handlers from the latest render, not the ones captured on mount', () => {
    const firstHandle = jest.fn();
    const secondHandle = jest.fn();
    const { rerender } = render(<Probe handleApi={firstHandle} />);

    rerender(<Probe handleApi={secondHandle} />);
    history.push('/templates/1#api');

    expect(firstHandle).not.toHaveBeenCalled();
    expect(secondHandle).toHaveBeenCalledTimes(1);
  });
});
