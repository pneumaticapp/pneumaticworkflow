import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { SubMenuTooltip } from '../SubMenuItemTooltip';
import styles from '../SubMenuItemTooltip.css';

jest.mock('../../UI', () => ({
  Tooltip: ({ size, children }: { size?: string; children: React.ReactNode }) => (
    <div data-testid="tooltip" data-size={size}>
      {children}
    </div>
  ),
}));

describe('SubMenuTooltip', () => {
  const renderTooltip = () =>
    render(
      <SubMenuTooltip containerClassName="menu-default" menuItems={[]}>
        <a href="/help">Help center</a>
      </SubMenuTooltip>,
    );

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('uses the large arrow that matches the submenu caret dimensions', () => {
    renderTooltip();

    expect(screen.getByTestId('tooltip')).toHaveAttribute('data-size', 'lg');
  });

  it('uses a full-width element as the tooltip trigger', () => {
    renderTooltip();

    const trigger = screen.getByTestId('sub-menu-trigger');

    expect(trigger).toBeInstanceOf(HTMLDivElement);
    expect(trigger).toHaveClass(styles['sub-menu__trigger']);
  });
});
