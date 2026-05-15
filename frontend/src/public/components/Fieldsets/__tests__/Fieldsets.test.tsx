// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { Fieldsets } from '../Fieldsets';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import {
  loadFieldsets,
  setTemplateId,
} from '../../../redux/fieldsets/slice';

jest.mock('../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../redux/fieldsets/slice', () => ({
  openCreateModal: jest.fn(() => ({ type: 'fieldsets/openCreateModal' })),
  loadFieldsets: jest.fn((p) => ({ type: 'fieldsets/loadFieldsets', payload: p })),
  setTemplateId: jest.fn((p) => ({ type: 'fieldsets/setTemplateId', payload: p })),
}));

jest.mock('react-infinite-scroll-component', () => ({
  __esModule: true,
  default: jest.fn(({ children }) => React.createElement('div', null, children)),
}));

jest.mock('../../PageTitle', () => ({
  PageTitle: jest.fn(() => null),
}));

jest.mock('../../UI', () => ({
  AddCardButton: jest.fn(() => null),
}));

jest.mock('../../icons', () => ({
  AIPlusIcon: () => null,
}));

jest.mock('../FieldsetModal/FieldsetModal', () => ({
  FieldsetModal: jest.fn(() => null),
}));

jest.mock('../FieldsetModal/types', () => ({
  EFieldsetModalType: { Create: 'create', Edit: 'edit' },
}));

jest.mock('../FieldsetCard', () => ({
  FieldsetCard: jest.fn(() => null),
}));

describe('Fieldsets', () => {
  const mockDispatch = jest.fn();

  const makeProps = (templateId: string = '5') => ({
    match: { params: { templateId }, isExact: true, path: '', url: '' },
    location: {
      pathname: `/templates/${templateId}/fieldsets/`,
      search: '',
      hash: '',
      state: undefined,
    },
    history: history as any,
  });

  const defaultState = {
    fieldsets: {
      fieldsetsList: { items: [], count: 0, offset: 0 },
      isFieldsetsLoading: false,
      fieldsetsListSorting: '-date_created_tsp',
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockImplementation((selector) => selector(defaultState));
  });

  describe('URL parameter validation', () => {
    it('redirects to /templates/ when templateId is NaN', () => {
      render(React.createElement(Fieldsets, makeProps('abc')));

      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(ERoutes.Templates);
      expect(setTemplateId).not.toHaveBeenCalled();
      expect(loadFieldsets).not.toHaveBeenCalled();
    });

    it('dispatches setTemplateId and loadFieldsets when templateId is valid', () => {
      render(React.createElement(Fieldsets, makeProps('5')));

      expect(history.push).not.toHaveBeenCalled();
      expect(mockDispatch).toHaveBeenCalledWith(setTemplateId(5));
      expect(mockDispatch).toHaveBeenCalledWith(loadFieldsets({ offset: 0, templateId: 5 }));
    });
  });
});
