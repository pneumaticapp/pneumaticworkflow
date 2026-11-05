import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { LogoCircle } from '../LogoCircle';

const SVG_TEST_ID = 'logo-circle';
const CIRCLE_TEST_ID = 'logo-circle-background';
const PATH_TEST_ID = 'logo-circle-mark';

describe('LogoCircle', () => {
  it('renders svg with size 40 by default', () => {
    render(<LogoCircle />);

    const svg = screen.getByTestId(SVG_TEST_ID);
    expect(svg).toHaveAttribute('width', '40');
    expect(svg).toHaveAttribute('height', '40');
    expect(svg).toHaveAttribute('viewBox', '0 0 40 40');
  });

  it('renders circle with center and radius equal to size / 2', () => {
    render(<LogoCircle size={96} />);

    const circle = screen.getByTestId(CIRCLE_TEST_ID);
    expect(circle).toHaveAttribute('cx', '48');
    expect(circle).toHaveAttribute('cy', '48');
    expect(circle).toHaveAttribute('r', '48');
  });

  it('passes className to svg', () => {
    render(<LogoCircle className="test" />);

    expect(screen.getByTestId(SVG_TEST_ID)).toHaveClass('test');
  });

  it('scales mark when size is not 48', () => {
    render(<LogoCircle size={96} />);

    expect(screen.getByTestId(PATH_TEST_ID)).toHaveStyle({ transform: 'scale(calc(96 / 48))' });
  });

  it('uses dark theme colors by default', () => {
    render(<LogoCircle />);

    expect(screen.getByTestId(CIRCLE_TEST_ID)).toHaveAttribute('fill', 'var(--pneumatic-color-black100)');
    expect(screen.getByTestId(PATH_TEST_ID)).toHaveAttribute('fill', 'var(--pneumatic-color-link)');
  });
});
