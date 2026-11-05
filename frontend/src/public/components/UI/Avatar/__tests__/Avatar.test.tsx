import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { Avatar } from '../Avatar';

describe('Avatar', () => {
  it('renders profile image when photo is provided', () => {
    const url = '/some/image.png';
    const user = {
      firstName: '',
      lastName: '',
      photo: url,
      email: '',
    };

    render(<Avatar user={user} />);

    expect(screen.getByRole('img', { name: 'Profile' })).toHaveAttribute('src', url);
  });

  it('renders initials from first and last name', () => {
    const user = {
      firstName: 'Test',
      lastName: 'User',
      photo: '',
      email: 'test@test.com',
    };

    render(<Avatar user={user} />);

    expect(screen.getByText('TU')).toBeInTheDocument();
  });

  it('renders no initials when name is not provided', () => {
    const user = {
      firstName: '',
      lastName: '',
      photo: '',
      email: '',
    };

    render(<Avatar user={user} />);

    expect(screen.getByTestId('avatar-initials')).toBeEmptyDOMElement();
  });

  describe('group avatar', () => {
    const groupUser = {
      firstName: '',
      lastName: '',
      photo: '',
      email: '',
      type: 'group' as const,
    };

    it('applies containerClassName to root element', () => {
      render(<Avatar user={groupUser} containerClassName="avatar-container" />);

      expect(screen.getByTestId('avatar')).toHaveClass('avatar-container');
    });

    it('renders group icon', () => {
      render(<Avatar user={groupUser} containerClassName="avatar-container" />);

      expect(screen.getByTestId('avatar-group-icon')).toBeInTheDocument();
    });

    it('does not nest group icon in extra container', () => {
      render(<Avatar user={groupUser} containerClassName="avatar-container" />);

      const root = screen.getByTestId('avatar');
      const groupIcon = screen.getByTestId('avatar-group-icon');

      expect(groupIcon.parentElement).toBe(root);
    });
  });
});
