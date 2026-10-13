import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';
import { useDispatch } from 'react-redux';

import { enMessages } from '../../../lang/locales/en_US';
import { IAuthUser } from '../../../types/redux';
import { Profile } from '../Profile';

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: jest.fn(),
}));

jest.mock('../AvatarController', () => ({ AvatarController: () => null }));
jest.mock('../ChangePassword', () => ({ ChangePassword: () => null }));
jest.mock('../ProfileManager', () => ({ ProfileManager: () => null }));
jest.mock('../ProfileReports', () => ({ ProfileReports: () => null }));
jest.mock('../ProfileVacationFields', () => ({ ProfileVacationFields: () => null }));
jest.mock('../../UI/Fields/Checkbox', () => ({ FormikCheckbox: () => null }));
jest.mock('../../UI', () => ({ FormikDropdownList: () => null }));

const user = {
  id: 1,
  email: 'user@example.com',
  firstName: 'Test',
  lastName: 'User',
  phone: '',
  loading: false,
  isDigestSubscriber: false,
  isTasksDigestSubscriber: false,
  isCommentsMentionsSubscriber: false,
  isNewTasksSubscriber: false,
  isNewslettersSubscriber: false,
  isSpecialOffersSubscriber: false,
  language: 'en',
  timezone: 'UTC',
  dateFdw: '0',
  dateFmt: 'MMM dd, yyy, p',
  isAdmin: false,
  managerId: null,
  reportIds: [],
} as unknown as IAuthUser;

describe('Profile', () => {
  it('does not save an empty phone number', async () => {
    const editCurrentUser = jest.fn();
    (useDispatch as jest.Mock).mockReturnValue(jest.fn());

    render(
      <IntlProvider locale="en" messages={enMessages}>
        <Profile
          user={user}
          editCurrentUser={editCurrentUser}
          sendChangePassword={jest.fn()}
          onChangeTab={jest.fn()}
          onVacationActivate={jest.fn()}
          onVacationDeactivate={jest.fn()}
          availableUsers={[]}
        />
      </IntlProvider>,
    );

    expect(screen.getByText('Phone number')).toHaveClass('title_required');

    userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => {
      expect(screen.getByText('Please enter your phone')).toBeInTheDocument();
    });
    expect(editCurrentUser).not.toHaveBeenCalled();
  });
});
