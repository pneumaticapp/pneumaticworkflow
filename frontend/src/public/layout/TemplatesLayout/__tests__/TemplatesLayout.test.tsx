import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { TemplatesLayout } from '../TemplatesLayout';
import { SelectMenu } from '../../../components/UI';
import { setFieldsetsListSorting } from '../../../redux/fieldsets/slice';
import { EFieldsetsSorting } from '../../../types/fieldset';
import { fieldsetsSortingValues } from '../../../constants/sortings';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

jest.mock('../../../components/TopNav', () => ({
  TopNavContainer: jest.fn(({ leftContent }: { leftContent: React.ReactNode }) =>
    require('react').createElement('div', { 'data-testid': 'topnav' }, leftContent),
  ),
}));

jest.mock('../../../components/UI', () => ({
  SelectMenu: jest.fn(() => null),
  Tabs: jest.fn(() => null),
}));

jest.mock('../../../components/UI/ReturnLink', () => ({
  ReturnLink: jest.fn(() => null),
}));

jest.mock('../TemplatesSortingContainer', () => ({
  TemplatesSortingContainer: jest.fn(() => null),
}));

jest.mock('../../../utils/history', () => ({
  history: {
    location: { pathname: '/' },
    push: jest.fn(),
  },
}));

jest.mock('../../../redux/fieldsets/slice', () => ({
  setFieldsetsListSorting: jest.fn((payload: string) => ({
    type: 'fieldsets/setFieldsetsListSorting',
    payload,
  })),
}));

jest.mock('../../../redux/datasets/slice', () => ({
  setDatasetsListSorting: jest.fn((payload: string) => ({
    type: 'datasets/setDatasetsListSorting',
    payload,
  })),
}));

jest.mock('../../../redux/selectors/fieldsets', () => ({
  getFieldsetsSorting: jest.fn(),
}));

jest.mock('../../../redux/selectors/datasets', () => ({
  getDatasetsSorting: jest.fn(),
}));

describe('TemplatesLayout — fieldsets sorting', () => {
  const mockDispatch = jest.fn();

  const setPathname = (url: string) => {
    (history.location as { pathname: string }).pathname = url;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockReturnValue(EFieldsetsSorting.DateDesc);
  });

  it('renders sorting SelectMenu with fieldsets values on fieldsets tab', () => {
    setPathname(ERoutes.Fieldsets);

    render(React.createElement(TemplatesLayout, null, 'child'));

    const selectMenuMock = SelectMenu as jest.Mock;
    const fieldsetsCalls = selectMenuMock.mock.calls.filter(
      (call: [Record<string, unknown>]) => call[0].values === fieldsetsSortingValues,
    );
    expect(fieldsetsCalls.length).toBe(1);
    expect(fieldsetsCalls[0][0]).toEqual(
      expect.objectContaining({
        activeValue: EFieldsetsSorting.DateDesc,
        values: fieldsetsSortingValues,
        closeOnSelect: true,
      }),
    );
  });

  it('dispatches setFieldsetsListSorting when fieldsets sorting onChange is called', () => {
    setPathname(ERoutes.Fieldsets);

    render(React.createElement(TemplatesLayout, null, 'child'));

    const selectMenuMock = SelectMenu as jest.Mock;
    const fieldsetsCall = selectMenuMock.mock.calls.find(
      (call: [Record<string, unknown>]) => call[0].values === fieldsetsSortingValues,
    );
    const onChangeProp = fieldsetsCall[0].onChange as (value: EFieldsetsSorting) => void;

    onChangeProp(EFieldsetsSorting.NameAsc);

    expect(setFieldsetsListSorting).toHaveBeenCalledTimes(1);
    expect(setFieldsetsListSorting).toHaveBeenCalledWith(EFieldsetsSorting.NameAsc);
    expect(mockDispatch).toHaveBeenCalledTimes(1);
  });
});
