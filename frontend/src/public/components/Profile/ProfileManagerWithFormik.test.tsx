// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';

import { Profile } from './Profile';
import { IAuthUser } from '../../types/redux';

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useSelector: jest.fn(),
  useDispatch: jest.fn(() => jest.fn()),
}));

jest.mock('./ProfileManager', () => ({
  ProfileManager: jest.fn(({ onManagerChange }: any) => (
    <button
      data-testid="change-manager-btn"
      onClick={() => onManagerChange(42)}
    >
      Change Manager
    </button>
  )),
}));

jest.mock('./ProfileReports', () => ({
  ProfileReports: jest.fn(() => <div data-testid="profile-reports" />),
}));

jest.mock('./AvatarController', () => ({
  AvatarController: jest.fn(() => <div data-testid="avatar-controller" />),
}));

jest.mock('./ChangePassword', () => ({
  ChangePassword: jest.fn(() => null),
}));

jest.mock('../UI/Buttons/Button', () => ({
  Button: ({ onClick, label, ...props }: any) => (
    <button onClick={onClick} data-testid={`btn-${label}`} {...props}>
      {label}
    </button>
  ),
}));

jest.mock('../UI/Fields/InputField', () => ({
  FormikInputField: ({ name, ...props }: any) => (
    <input data-testid={`input-${name}`} name={name} {...props} />
  ),
  InputField: ({ value, ...props }: any) => (
    <input data-testid="input-field" value={value || ''} readOnly {...props} />
  ),
}));

jest.mock('../UI', () => ({
  FormikDropdownList: jest.fn(() => <div data-testid="dropdown" />),
}));

jest.mock('../UI/Typeography/Header', () => ({
  Header: ({ children, ...props }: any) => <h1 {...props}>{children}</h1>,
}));

jest.mock('../UI/Typeography/SectionTitle', () => ({
  SectionTitle: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
}));

jest.mock('../UI/Fields/Checkbox', () => ({
  FormikCheckbox: jest.fn(() => <div data-testid="checkbox" />),
}));

jest.mock('../icons/LockIcon', () => ({
  LockIcon: () => <span data-testid="lock-icon" />,
}));

jest.mock('../../redux/accounts/slice', () => ({
  teamFetchStarted: jest.fn(() => ({ type: 'teamFetchStarted' })),
  usersFetchStarted: jest.fn(() => ({ type: 'usersFetchStarted' })),
}));

const makeUser = (overrides: Partial<IAuthUser> = {}): IAuthUser => ({
  id: 1,
  email: 'test@test.com',
  firstName: 'PropFirst',
  lastName: 'PropLast',
  phone: '111-prop',
  loading: false,
  isDigestSubscriber: true,
  isTasksDigestSubscriber: true,
  isCommentsMentionsSubscriber: true,
  isNewTasksSubscriber: true,
  isNewslettersSubscriber: true,
  isSpecialOffersSubscriber: true,
  language: 'en',
  timezone: 'UTC',
  dateFdw: '0',
  dateFmt: '%m/%d/%Y, %I:%M %p',
  isAdmin: false,
  isAccountOwner: false,
  managerId: null,
  reportIds: [],
  ...overrides,
} as IAuthUser);

describe('Profile — ProfileManagerSection', () => {
  const mockEditCurrentUser = jest.fn();
  const mockSendChangePassword = jest.fn();
  const mockOnChangeTab = jest.fn();
  const mockOnVacationActivate = jest.fn();
  const mockOnVacationDeactivate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockReturnValue([]);
  });

  it('sends only managerId when changing manager', () => {
    // arrange
    const user = makeUser();

    // act
    render(
      <Profile
        user={user}
        editCurrentUser={mockEditCurrentUser}
        sendChangePassword={mockSendChangePassword}
        onChangeTab={mockOnChangeTab}
        onVacationActivate={mockOnVacationActivate}
        onVacationDeactivate={mockOnVacationDeactivate}
        availableUsers={[]}
      />
    );

    userEvent.click(screen.getByTestId('change-manager-btn'));

    // assert
    expect(mockEditCurrentUser).toHaveBeenCalledTimes(1);
    expect(mockEditCurrentUser).toHaveBeenCalledWith({ managerId: 42 });
  });

  it('does not include profile fields in manager change request', () => {
    // arrange
    const user = makeUser();

    // act
    render(
      <Profile
        user={user}
        editCurrentUser={mockEditCurrentUser}
        sendChangePassword={mockSendChangePassword}
        onChangeTab={mockOnChangeTab}
        onVacationActivate={mockOnVacationActivate}
        onVacationDeactivate={mockOnVacationDeactivate}
        availableUsers={[]}
      />
    );

    userEvent.click(screen.getByTestId('change-manager-btn'));

    // assert
    expect(mockEditCurrentUser).toHaveBeenCalledTimes(1);
    const callArgs = mockEditCurrentUser.mock.calls[0][0];
    expect(callArgs).not.toHaveProperty('firstName');
    expect(callArgs).not.toHaveProperty('lastName');
    expect(callArgs).not.toHaveProperty('phone');
    expect(callArgs).not.toHaveProperty('dateFmt');
  });
});
