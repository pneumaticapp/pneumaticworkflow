import React from 'react';
import { render, screen } from '@testing-library/react';

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
});
