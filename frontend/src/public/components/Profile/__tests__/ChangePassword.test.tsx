import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { enMessages } from '../../../lang/locales/en_US';
import { ChangePassword } from '../ChangePassword';

describe('ChangePassword', () => {
  it('marks an empty password confirmation as invalid', async () => {
    const sendChangePassword = jest.fn();

    render(
      <IntlProvider locale="en" messages={enMessages}>
        <ChangePassword
          isOpen
          handleCloseModal={jest.fn()}
          sendChangePassword={sendChangePassword}
          loading={false}
        />
      </IntlProvider>,
    );

    expect(screen.getByText('Old password')).toHaveClass('title_required');
    expect(screen.getByText('New password')).toHaveClass('title_required');
    expect(screen.getByText('New password (confirm)')).toHaveClass('title_required');

    userEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(screen.getByText('New password (confirm)').parentElement).toHaveTextContent(
        'Please enter your new password',
      );
    });
    expect(sendChangePassword).not.toHaveBeenCalled();
  });
});
