import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { enMessages } from '../../../../../lang/locales/en_US';
import { DropdownButton } from '../DropdownButton';

describe('DropdownButton', () => {
  it('runs an action and closes its shared dropdown', () => {
    const onClick = jest.fn();
    render(
      <IntlProvider locale="en" messages={enMessages}>
        <DropdownButton dropdownOptions={[{ itemHeaderIntlId: 'general.modify', onClick }]} />
      </IntlProvider>,
    );

    fireEvent.click(screen.getByRole('button'));
    fireEvent.click(screen.getByRole('button', { name: 'Modify' }));

    expect(onClick).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });
});
