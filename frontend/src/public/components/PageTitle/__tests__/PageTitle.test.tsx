import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { PageTitle } from '../PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';
import { intlMock } from '../../../__stubs__/intlMock';

type TTooltipMockProps = {
  content: React.ReactNode;
  children: React.ReactNode;
};

type THeaderMockProps = {
  children: React.ReactNode;
};

jest.mock('../../UI', () => ({
  Tooltip: ({ content, children }: TTooltipMockProps) => (
    <div data-testid="tooltip-wrapper">
      {children}
      <div data-testid="tooltip-content">{content}</div>
    </div>
  ),
  Header: ({ children }: THeaderMockProps) => <h1>{children}</h1>,
}));

jest.mock('../../icons', () => ({
  FilledInfoIcon: () => null,
}));

describe('PageTitle for the Fieldsets page', () => {
  it('renders the localized "Fieldsets" heading', () => {
    render(<PageTitle titleId={EPageTitle.Fieldsets} />);

    const expectedTitle = intlMock.formatMessage({ id: EPageTitle.Fieldsets });
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(expectedTitle);
  });

  it('renders the localized fieldsets tooltip content', () => {
    render(<PageTitle titleId={EPageTitle.Fieldsets} />);

    const expectedTooltip = intlMock.formatMessage({ id: 'fieldsets.title.tooltip' });
    const tooltipContent = screen.getByTestId('tooltip-content');
    expect(tooltipContent).toHaveTextContent(expectedTooltip);
  });

  it('does not render a "Learn more" link in the tooltip content', () => {
    render(<PageTitle titleId={EPageTitle.Fieldsets} />);

    expect(screen.queryByRole('link')).toBeNull();
    expect(screen.queryByText(/learn more/i)).toBeNull();
  });
});
