// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { TemplateLayout } from '../TemplateLayout';
import { ReturnLink, SelectMenu } from '../../../components/UI';
import { setFieldsetsListSorting } from '../../../redux/fieldsets/slice';
import { EFieldsetsSorting } from '../../../types/fieldset';
import { ERoutes } from '../../../constants/routes';
import { fieldsetsSortingValues } from '../../../constants/sortings';
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
  SelectMenu: jest.fn(() => null),
}));

jest.mock('../../../utils/history', () => ({
  history: {
    location: { pathname: '/' },
    listen: jest.fn(() => jest.fn()),
  },
}));

jest.mock('../../../redux/fieldsets/slice', () => ({
  setFieldsetsListSorting: jest.fn((payload: string) => ({
    type: 'fieldsets/setFieldsetsListSorting',
    payload,
  })),
}));

jest.mock('../../../redux/selectors/fieldsets', () => ({
  getFieldsetsSorting: jest.fn(),
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
  const mockDispatch = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const BACK_TO_TEMPLATE = formatMsg('fieldsets.back-to-template');
  const BREADCRUMB_TEMPLATE = formatMsg('fieldsets.breadcrumb.template');
  const BREADCRUMB_FIELDSETS = formatMsg('fieldsets.breadcrumb.fieldsets');
  const BACK_TO_TEMPLATES = formatMsg('menu.templates');

  const setPathname = (url: string) => {
    (history.location as { pathname: string }).pathname = url;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockReturnValue(EFieldsetsSorting.DateDesc);
  });

  it('renders ReturnLink to template and sorting SelectMenu on fieldsets list path', () => {
    setPathname('/templates/42/fieldsets/');

    render(React.createElement(TemplateLayout, null, 'child'));

    expect(ReturnLink as jest.Mock).toHaveBeenCalledTimes(1);
    expect(ReturnLink as jest.Mock).toHaveBeenCalledWith(
      expect.objectContaining({
        label: BACK_TO_TEMPLATE,
        route: '/templates/edit/42/',
      }),
      {},
    );

    expect(SelectMenu as jest.Mock).toHaveBeenCalledTimes(1);
    expect(SelectMenu as jest.Mock).toHaveBeenCalledWith(
      expect.objectContaining({
        activeValue: EFieldsetsSorting.DateDesc,
        values: fieldsetsSortingValues,
        closeOnSelect: true,
      }),
      {},
    );
  });

  it('dispatches setFieldsetsListSorting when SelectMenu onChange is called', () => {
    setPathname('/templates/42/fieldsets/');

    render(React.createElement(TemplateLayout, null, 'child'));

    const selectMenuMock = SelectMenu as jest.Mock;
    const onChangeProp = selectMenuMock.mock.calls[0][0].onChange;

    onChangeProp(EFieldsetsSorting.NameAsc);

    const mockedSetSorting = setFieldsetsListSorting as jest.MockedFunction<typeof setFieldsetsListSorting>;
    expect(mockedSetSorting).toHaveBeenCalledTimes(1);
    expect(mockedSetSorting).toHaveBeenCalledWith(EFieldsetsSorting.NameAsc);
    expect(mockDispatch).toHaveBeenCalledTimes(1);
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

    expect(SelectMenu as jest.Mock).toHaveBeenCalledTimes(0);
  });

  it('renders single ReturnLink to templates list without SelectMenu on template path', () => {
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

    expect(SelectMenu as jest.Mock).toHaveBeenCalledTimes(0);
  });
});
