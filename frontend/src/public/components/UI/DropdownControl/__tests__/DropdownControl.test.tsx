import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { DropdownArea } from '../../DropdownArea';
import styles from '../DropdownControl.css';

describe('DropdownControl', () => {
  it('is shared by the Add guest dropdown area', () => {
    render(
      <DropdownArea title="Add guest">
        <div>Guest form</div>
      </DropdownArea>,
    );

    expect(screen.getByText('Add guest')).toHaveClass(styles['dropdown-control__value']);
  });

  it('opens and dismisses DropdownArea content through the shared behavior', () => {
    render(
      <DropdownArea title="Add guest">
        <div>Guest form</div>
      </DropdownArea>,
    );

    expect(screen.queryByText('Guest form')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Add guest' }));
    expect(screen.getByText('Guest form')).toBeInTheDocument();

    fireEvent.mouseDown(document.body);
    expect(screen.queryByText('Guest form')).not.toBeInTheDocument();
  });
});
