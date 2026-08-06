import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { ETaskListSorting } from '../../../../types/tasks';
import { SelectMenu } from '../SelectMenu';

jest.mock('../../../icons', () => ({ ExpandIcon: () => null }));
jest.mock('../../../IntlMessages', () => ({
  IntlMessages: ({ id, children }: { id: string; children?: (text: string) => React.ReactNode }) => (
    <>{children ? children(id) : id}</>
  ),
}));

const mockProps = {
  activeValue: ETaskListSorting.DateDesc,
  values: Object.values(ETaskListSorting),
  onChange: jest.fn(),
};

describe('SelectMenu', () => {
  beforeEach(() => jest.clearAllMocks());

  it('calls onChange for an inactive value', () => {
    render(<SelectMenu {...mockProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'sorting.date-desc' }));
    fireEvent.click(screen.getByRole('menuitemradio', { name: 'sorting.date-asc' }));

    expect(mockProps.onChange).toHaveBeenCalledWith(ETaskListSorting.DateAsc);
  });

  it('does not call onChange for the active value', () => {
    render(<SelectMenu {...mockProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'sorting.date-desc' }));
    fireEvent.click(screen.getByRole('menuitemradio', { name: 'sorting.date-desc' }));

    expect(mockProps.onChange).not.toHaveBeenCalled();
  });
});
