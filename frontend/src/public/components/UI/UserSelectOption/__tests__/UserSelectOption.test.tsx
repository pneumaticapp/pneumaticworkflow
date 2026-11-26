import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { UserSelectOption } from '../UserSelectOption';
import { Avatar } from '../../Avatar';
import { makeUser } from '../../../../__stubs__/users.factory';

jest.mock('../../Avatar', () => ({
  Avatar: jest.fn(() => <span data-testid="avatar" />),
}));

describe('UserSelectOption', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders user name and passes user with size="sm" to Avatar', () => {
    const user = makeUser({ id: 1, firstName: 'Alice', lastName: 'Smith' });

    render(<UserSelectOption user={user} name="Alice Smith" />);

    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.getByTestId('avatar')).toBeInTheDocument();

    const avatarMock = Avatar as jest.Mock;
    expect(avatarMock).toHaveBeenCalledTimes(1);
    expect(avatarMock).toHaveBeenCalledWith(expect.objectContaining({ user, size: 'sm' }), {});
  });

  it('renders group name and passes group avatar type with size="sm" to Avatar', () => {
    const groupAvatar = { type: 'group' as const };

    render(<UserSelectOption user={groupAvatar} name="Sales Team" />);

    expect(screen.getByText('Sales Team')).toBeInTheDocument();
    expect(screen.getByTestId('avatar')).toBeInTheDocument();

    const avatarMock = Avatar as jest.Mock;
    expect(avatarMock).toHaveBeenCalledTimes(1);
    expect(avatarMock).toHaveBeenCalledWith(expect.objectContaining({ user: groupAvatar, size: 'sm' }), {});
  });
});
