import * as React from 'react';
import { render } from '@testing-library/react';
import { useSelector } from 'react-redux';

import { TemplateLayout } from '../TemplateLayout';
import { ReturnLink } from '../../../components/UI';
import { ERoutes } from '../../../constants/routes';
import { intlMock } from '../../../__stubs__/intlMock';
import { history } from '../../../utils/history';

type TTopNavMockProps = { leftContent: React.ReactNode };

jest.mock('../../../components/TopNav', () => ({
  TopNavContainer: jest.fn(({ leftContent }: TTopNavMockProps) =>
    require('react').createElement('div', { 'data-testid': 'topnav' }, leftContent),
  ),
}));

jest.mock('../../../components/UI', () => ({
  ReturnLink: jest.fn(() => null),
}));

jest.mock('../../../utils/history', () => ({
  history: {
    location: { pathname: '/' },
    listen: jest.fn(() => jest.fn()),
  },
}));


jest.mock('../../../utils/routes/getLinkToTemplate', () => ({
  getLinkToTemplate: jest.fn(({ templateId }: { templateId: number }) =>
    `/templates/edit/${templateId}/`,
  ),
}));

jest.mock('../../../utils/routes/getLinkToFieldsets', () => ({
  getLinkToFieldsets: jest.fn((templateId: number) =>
    `/templates/${templateId}/fieldsets/`,
  ),
}));

describe('TemplateLayout — fieldsets navigation', () => {
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const BREADCRUMB_TEMPLATE = formatMsg('fieldsets.breadcrumb.template');
  const BREADCRUMB_FIELDSETS = formatMsg('fieldsets.breadcrumb.fieldsets');
  const BACK_TO_TEMPLATES = formatMsg('menu.templates');

  const setPathname = (url: string) => {
    (history.location as { pathname: string }).pathname = url;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockReturnValue(null);
  });

  it('renders two breadcrumb ReturnLinks on fieldset detail path', () => {
    setPathname('/templates/42/fieldsets/7/');

    render(React.createElement(TemplateLayout, null, 'child'));

    expect(ReturnLink as jest.Mock).toHaveBeenCalledTimes(2);
    expect(ReturnLink as jest.Mock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        label: BREADCRUMB_TEMPLATE,
        route: '/templates/edit/42/',
      }),
      {},
    );
    expect(ReturnLink as jest.Mock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        label: BREADCRUMB_FIELDSETS,
        route: '/templates/42/fieldsets/',
      }),
      {},
    );
  });

  it('renders single ReturnLink to templates list on fieldsets list path', () => {
    setPathname('/templates/42/fieldsets/');

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

  it('renders single ReturnLink to templates list on template path', () => {
    setPathname('/templates/42/');

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
});
