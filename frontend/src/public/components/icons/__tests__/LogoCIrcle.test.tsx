import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { LogoCircle } from '../LogoCircle';
import { BRAND } from '../../../constants/branding';

const SVG_TEST_ID = 'logo-circle';

describe('LogoCircle', () => {
  it('renders svg with size 40 by default', () => {
    render(<LogoCircle />);

    const svg = screen.getByTestId(SVG_TEST_ID);
    expect(svg).toHaveAttribute('width', '40');
    expect(svg).toHaveAttribute('height', '40');
    expect(svg).toHaveAttribute('viewBox', '0 0 40 40');
  });

  it('contains the complete supplied emblem instead of cropping it into a circle', () => {
    const { container } = render(<LogoCircle size={96} />);
    const image = container.querySelector('image');

    expect(image).toHaveAttribute('width', '96');
    expect(image).toHaveAttribute('height', '96');
    expect(image).toHaveAttribute('preserveAspectRatio', 'xMidYMid meet');
    expect(container.querySelector('circle')).toBeNull();
  });

  it('passes className to svg', () => {
    render(<LogoCircle className="test" />);

    expect(screen.getByTestId(SVG_TEST_ID)).toHaveClass('test');
  });

  it('exposes the product and organization without mirroring official artwork', () => {
    const { container } = render(<LogoCircle size={32} />);

    expect(screen.getByTestId(SVG_TEST_ID)).toHaveAccessibleName(`${BRAND.name} — ${BRAND.organization}`);
    expect(container.querySelector('image')).not.toHaveAttribute('transform');
  });

  it('uses the supplied black/gold versions for light surfaces and the sidebar', () => {
    const { container, rerender } = render(<LogoCircle />);
    expect(container.querySelector('image')).toHaveAttribute('href', expect.stringContaining('eagle-black.svg'));
    rerender(<LogoCircle theme="light" />);
    expect(container.querySelector('image')).toHaveAttribute('href', expect.stringContaining('eagle-gold.svg'));
  });
});
