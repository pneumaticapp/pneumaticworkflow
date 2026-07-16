import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { TemplateLayout } from '../TemplateLayout';
import { ReturnLink } from '../../../components/UI';
import { ERoutes } from '../../../constants/routes';
import { intlMock } from '../../../__stubs__/intlMock';

type TTopNavMockProps = { leftContent: React.ReactNode };

jest.mock('../../../components/TopNav', () => ({
  TopNavContainer: jest.fn(({ leftContent }: TTopNavMockProps) =>
    require('react').createElement('div', { 'data-testid': 'topnav' }, leftContent),
  ),
}));

jest.mock('../../../components/UI', () => ({
  ReturnLink: jest.fn(() => null),
}));

describe('TemplateLayout', () => {
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const BACK_TO_TEMPLATES = formatMsg('menu.templates');

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders single ReturnLink to templates list', () => {
    render(React.createElement(TemplateLayout, null, 'child'));

    expect(ReturnLink as jest.Mock).toHaveBeenCalledTimes(1);
    expect(ReturnLink as jest.Mock).toHaveBeenCalledWith(
      expect.objectContaining({
        label: BACK_TO_TEMPLATES,
        route: ERoutes.Templates,
      }),
      {},
    );
  });

  it('renders children content', () => {
    render(
      React.createElement(TemplateLayout, null, 'test-child-content'),
    );

    expect(screen.getByText('test-child-content')).toBeInTheDocument();
  });
});
