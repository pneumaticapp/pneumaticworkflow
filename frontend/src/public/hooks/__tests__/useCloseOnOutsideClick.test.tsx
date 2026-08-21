import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { useCloseOnOutsideClick } from '../useCloseOnOutsideClick';

const Probe = ({ onClose }: { onClose: () => void }) => {
  const ref = React.useRef<HTMLDivElement>(null);
  useCloseOnOutsideClick(ref, onClose);

  return (
    <div>
      <button type="button">outside</button>
      <div ref={ref}>inside</div>
    </div>
  );
};

describe('useCloseOnOutsideClick', () => {
  it('should call onClose when the pointer is outside the node', () => {
    const onClose = jest.fn();
    render(<Probe onClose={onClose} />);

    userEvent.click(screen.getByRole('button', { name: 'outside' }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should not call onClose when the pointer is inside the node', () => {
    const onClose = jest.fn();
    render(<Probe onClose={onClose} />);

    userEvent.click(screen.getByText('inside'));

    expect(onClose).not.toHaveBeenCalled();
  });
});
