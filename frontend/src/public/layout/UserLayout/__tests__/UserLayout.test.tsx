import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { UserLayout } from '../UserLayout';
import { BRAND } from '../../../constants/branding';

jest.mock('../../../utils/history', () => ({
  history: { location: { pathname: jest.requireActual('../../../constants/routes').ERoutes.Login } },
}));

describe('UserLayout brand integration', () => {
  it('keeps the wide default logo and existing form content', () => {
    render(
      <UserLayout pages={[]}>
        <button type="button">Sign in</button>
      </UserLayout>,
    );

    expect(screen.getByRole('img')).toHaveAttribute('width', '210');
    expect(screen.getByRole('img')).toHaveAttribute('height', '60');
    expect(screen.getByRole('img')).toHaveAccessibleName(`${BRAND.name} — ${BRAND.organization}`);
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
  });

  it('keeps configured welcome content and uses the internal application home for its emblem link', () => {
    render(<UserLayout pages={[{ slug: 'signin', title: 'Welcome', description: 'Existing page content' }]} />);

    expect(screen.getByRole('heading', { name: 'Welcome' })).toBeInTheDocument();
    expect(screen.getByText('Existing page content')).toBeInTheDocument();
    expect(screen.getByRole('link')).toHaveAttribute('href', BRAND.homePath);
    expect(screen.getByRole('img')).toHaveAttribute('width', '170');
    expect(screen.getByRole('img')).toHaveAttribute('height', '40');
    expect(screen.getByText(BRAND.name)).toBeInTheDocument();
    expect(screen.getByText(BRAND.organization)).toBeInTheDocument();
  });
});
