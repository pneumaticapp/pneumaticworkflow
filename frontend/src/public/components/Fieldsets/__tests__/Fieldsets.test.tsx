import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { Fieldsets } from '../Fieldsets';
import { FieldsetCard } from '../FieldsetCard';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { AddCardButton } from '../../UI';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import {
  openCreateModal,
  loadFieldsets,
  setTemplateId,
} from '../../../redux/fieldsets/slice';
import { intlMock } from '../../../__stubs__/intlMock';
import { EFieldsetsSorting, IFieldsetListItem } from '../../../types/fieldset';
import { makeFieldsetListItem } from '../../../__stubs__/fieldsets.factory';
import InfiniteScroll from 'react-infinite-scroll-component';

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
  default: jest.fn(({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'infinite-scroll' }, children),
  ),
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

  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const NEW_FIELDSET_TITLE = formatMsg('fieldsets.new-fieldset.title');

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


  const getAddCardButtonProps = () => {
    const mock = AddCardButton as unknown as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0];
  };

  const getInfiniteScrollProps = () => {
    const mock = InfiniteScroll as unknown as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0];
  };

  const defaultState = {
    fieldsets: {
      fieldsetsList: { items: [] as IFieldsetListItem[], count: 0, offset: 0 },
      isLoading: false,
      fieldsetsListSorting: EFieldsetsSorting.DateDesc,
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
      expect(mockDispatch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Loading state', () => {
    it('shows loading indicator when isLoading=true and list is empty', () => {
      const loadingState = {
        fieldsets: {
          ...defaultState.fieldsets,
          isLoading: true,
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(loadingState));

      const { container } = render(React.createElement(Fieldsets, makeProps('5')));

      expect(container.querySelector('.loading')).toBeInTheDocument();
    });

    it('does not show loading indicator when isLoading=true but list is not empty', () => {
      const loadingWithDataState = {
        fieldsets: {
          ...defaultState.fieldsets,
          isLoading: true,
          fieldsetsList: {
            items: [makeFieldsetListItem()],
            count: 1,
            offset: 0,
          },
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(loadingWithDataState));

      const { container } = render(React.createElement(Fieldsets, makeProps('5')));

      expect(container.querySelector('.loading')).not.toBeInTheDocument();
    });
  });

  describe('Fieldset cards rendering', () => {
    it('renders FieldsetCard for each fieldset with templateId', () => {
      const fieldsets = [
        makeFieldsetListItem({ id: 1, name: 'FS1' }),
        makeFieldsetListItem({ id: 2, apiName: 'fs-2', name: 'FS2' }),
      ];
      const stateWithData = {
        fieldsets: {
          ...defaultState.fieldsets,
          fieldsetsList: { items: fieldsets, count: 2, offset: 0 },
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(stateWithData));

      render(React.createElement(Fieldsets, makeProps('5')));

      const mock = FieldsetCard as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(2);
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ id: 1, name: 'FS1', templateId: 5 }), {});
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ id: 2, name: 'FS2', templateId: 5 }), {});
    });
  });

  describe('Create new fieldset', () => {
    it('dispatches openCreateModal when AddCardButton is clicked', () => {
      render(React.createElement(Fieldsets, makeProps('5')));

      const addCardProps = getAddCardButtonProps();
      expect(addCardProps.title).toBe(NEW_FIELDSET_TITLE);

      addCardProps.onClick();

      expect(mockDispatch).toHaveBeenCalledWith(openCreateModal());
    });
  });

  describe('Modals', () => {
    it('renders FieldsetModal for Create (with templateId) and Edit', () => {
      render(React.createElement(Fieldsets, makeProps('5')));

      const mock = FieldsetModal as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(2);
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ type: 'create', templateId: 5 }), {});
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ type: 'edit' }), {});
    });
  });

  describe('Pagination', () => {
    it('next() loads next page with offset+1 and templateId', () => {
      const stateWithOffset = {
        fieldsets: {
          ...defaultState.fieldsets,
          fieldsetsList: {
            items: [makeFieldsetListItem()],
            count: 10,
            offset: 2,
          },
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(stateWithOffset));

      render(React.createElement(Fieldsets, makeProps('5')));

      mockDispatch.mockClear();

      const scrollProps = getInfiniteScrollProps();
      scrollProps.next();

      expect(mockDispatch).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(loadFieldsets({ offset: 3, templateId: 5 }));
    });
  });

  describe('Sorting change', () => {
    it('reloads list when sorting changes', () => {
      const { rerender } = render(React.createElement(Fieldsets, makeProps('5')));

      expect(mockDispatch).toHaveBeenCalledWith(loadFieldsets({ offset: 0, templateId: 5 }));
      mockDispatch.mockClear();
      (loadFieldsets as unknown as jest.Mock).mockClear();

      const newSortingState = {
        fieldsets: {
          ...defaultState.fieldsets,
          fieldsetsListSorting: EFieldsetsSorting.NameAsc,
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(newSortingState));

      rerender(React.createElement(Fieldsets, makeProps('5')));

      expect(mockDispatch).toHaveBeenCalledWith(loadFieldsets({ offset: 0, templateId: 5 }));
    });
  });
});
