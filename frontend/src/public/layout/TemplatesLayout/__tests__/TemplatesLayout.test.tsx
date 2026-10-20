import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { TemplatesLayout } from '../TemplatesLayout';
import { DropdownList } from '../../../components/UI';
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
  DropdownList: jest.fn(() => null),
  Tabs: jest.fn(() => null),
}));

jest.mock('../../../components/UI/ReturnLink', () => ({
  ReturnLink: jest.fn(() => null),
}));

jest.mock('../TemplatesSorting', () => ({
  TemplatesSorting: jest.fn(() => null),
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

  const getFieldsetsSortingCalls = () =>
    (DropdownList as jest.Mock).mock.calls.filter(
      (call: [{ options: { value: string }[] }]) =>
        call[0].options.length === fieldsetsSortingValues.length &&
        call[0].options.every((option, index) => option.value === fieldsetsSortingValues[index]),
    );

  it('renders a compact sorting DropdownList with fieldsets values on fieldsets tab', () => {
    setPathname(ERoutes.Fieldsets);

    render(React.createElement(TemplatesLayout, null, 'child'));

    const fieldsetsCalls = getFieldsetsSortingCalls();
    expect(fieldsetsCalls.length).toBe(1);
    expect(fieldsetsCalls[0][0]).toEqual(
      expect.objectContaining({
        controlSize: 'sm',
        value: expect.objectContaining({ value: EFieldsetsSorting.DateDesc }),
      }),
    );
  });

  it('dispatches setFieldsetsListSorting when fieldsets sorting onChange is called', () => {
    setPathname(ERoutes.Fieldsets);

    render(React.createElement(TemplatesLayout, null, 'child'));

    const [fieldsetsCall] = getFieldsetsSortingCalls();
    const onChangeProp = fieldsetsCall[0].onChange as (option: { value: EFieldsetsSorting }) => void;

    onChangeProp({ value: EFieldsetsSorting.NameAsc });

    expect(setFieldsetsListSorting).toHaveBeenCalledTimes(1);
    expect(setFieldsetsListSorting).toHaveBeenCalledWith(EFieldsetsSorting.NameAsc);
    expect(mockDispatch).toHaveBeenCalledTimes(1);
  });
});
