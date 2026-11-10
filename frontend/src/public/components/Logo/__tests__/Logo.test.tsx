import * as React from 'react';
import { render, screen } from '@testing-library/react';
import * as ReactIntl from 'react-intl';

import { Logo } from '../Logo';
import { BrandLockup } from '../BrandLockup';
import { BRAND } from '../../../constants/branding';
import { PneumaticAvatarIcon } from '../../icons/PneumaticAvatarIcon';

jest.mock('react-intl', () => ({ ...jest.requireActual('react-intl'), useIntl: jest.fn() }));
const mockUseIntl = ReactIntl.useIntl as jest.MockedFunction<typeof ReactIntl.useIntl>;

describe('Ministry brand logos', () => {
  beforeEach(() => mockUseIntl.mockReturnValue(ReactIntl.createIntl({ locale: 'en' })));

  it('keeps the standard and wide footprints with product and ministry as separate text', () => {
    const { container, rerender } = render(<BrandLockup />);
    expect(screen.getByRole('img')).toHaveAttribute('width', '170');
    expect(screen.getByRole('img')).toHaveAttribute('height', '48');
    expect(container.querySelector('image')).toHaveAttribute('href', expect.stringContaining('eagle-black.svg'));
    expect(screen.getByText(BRAND.name)).toBeInTheDocument();
    expect(screen.getByText(BRAND.organization)).toBeInTheDocument();

    mockUseIntl.mockReturnValue(ReactIntl.createIntl({ locale: 'ar-SY' }));
    rerender(<BrandLockup variant="wide" tone="light" />);
    expect(screen.getByRole('img')).toHaveAttribute('width', '210');
    expect(screen.getByRole('img')).toHaveAttribute('height', '60');
    expect(screen.getByRole('img')).toHaveAccessibleName(`${BRAND.nameAr} — ${BRAND.organizationAr}`);
    expect(screen.getByText(BRAND.nameAr)).toBeInTheDocument();
    expect(screen.getByText(BRAND.organizationAr)).toBeInTheDocument();
    expect(container.querySelector('image')).toHaveAttribute('href', expect.stringContaining('eagle-white.svg'));
    expect(container.querySelector('image')).toHaveAttribute('preserveAspectRatio', 'xMidYMid meet');
  });

  it('keeps account-specific logos and their fixed standard footprints', () => {
    const { rerender } = render(
      <Logo size="lg" theme="light" partnerLogoLg="/account-wide.svg" partnerLogoSm="/account-mark.svg" />,
    );
    expect(screen.getByRole('img')).toHaveAttribute('src', '/account-wide.svg');
    expect(screen.getByRole('img')).toHaveAttribute('width', '170');
    expect(screen.getByRole('img')).toHaveAttribute('height', '48');

    rerender(<Logo size="sm" theme="light" partnerLogoLg="/account-wide.svg" partnerLogoSm="/account-mark.svg" />);
    expect(screen.getByRole('img')).toHaveAttribute('src', '/account-mark.svg');
    expect(screen.getByRole('img')).toHaveAttribute('width', '32');
    expect(screen.getByRole('img')).toHaveAttribute('height', '32');
  });

  it('uses the supplied eagle in system notifications within the existing avatar slot', () => {
    const { container } = render(<PneumaticAvatarIcon className="notification-avatar" />);
    expect(screen.getByRole('img')).toHaveAttribute('width', '32');
    expect(screen.getByRole('img')).toHaveAttribute('height', '32');
    expect(screen.getByRole('img')).toHaveClass('notification-avatar');
    expect(screen.getByRole('img')).toHaveAccessibleName(BRAND.name);
    expect(container.querySelector('image')).toHaveAttribute('href', expect.stringContaining('eagle-gold.svg'));
    expect(container.querySelector('image')).toHaveAttribute('preserveAspectRatio', 'xMidYMid meet');
    expect(container.querySelector('path')).toBeNull();
  });
});
