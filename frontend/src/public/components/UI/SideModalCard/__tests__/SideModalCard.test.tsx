import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { SideModalCard } from '../SideModalCard';

describe('SideModalCard', () => {
  const onClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls onClick once when the card is clicked', () => {
    render(<SideModalCard onClick={onClick} />);

    userEvent.click(screen.getByRole('button'));

    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
