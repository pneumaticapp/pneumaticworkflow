import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { Fieldsets } from '../Fieldsets';
import { FieldsetCard } from '../FieldsetCard';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { AddCardButton } from '../../UI';
import {
  openCreateModal,
  loadFieldsets,
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

  describe('Initial load', () => {
    it('dispatches loadFieldsets on mount', () => {
      render(React.createElement(Fieldsets));

      expect(mockDispatch).toHaveBeenCalledWith(loadFieldsets({ offset: 0 }));
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

      render(React.createElement(Fieldsets));

      expect(screen.getByTestId('fieldsets-loading')).toBeInTheDocument();
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

      render(React.createElement(Fieldsets));

      expect(screen.queryByTestId('fieldsets-loading')).not.toBeInTheDocument();
    });
  });

  describe('Fieldset cards rendering', () => {
    it('renders FieldsetCard for each fieldset with MOCK_TEMPLATE_ID', () => {
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

      render(React.createElement(Fieldsets));

      const mock = FieldsetCard as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(2);
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ id: 1, name: 'FS1', templateId: 1 }), {});
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ id: 2, name: 'FS2', templateId: 1 }), {});
    });
  });

  describe('Create new fieldset', () => {
    it('dispatches openCreateModal when AddCardButton is clicked', () => {
      render(React.createElement(Fieldsets));

      const addCardProps = getAddCardButtonProps();
      expect(addCardProps.title).toBe(NEW_FIELDSET_TITLE);

      addCardProps.onClick();

      expect(mockDispatch).toHaveBeenCalledWith(openCreateModal());
    });
  });

  describe('Modals', () => {
    it('renders FieldsetModal for Create (with MOCK_TEMPLATE_ID) and Edit', () => {
      render(React.createElement(Fieldsets));

      const mock = FieldsetModal as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(2);
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ type: 'create', templateId: 1 }), {});
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ type: 'edit' }), {});
    });
  });

  describe('Pagination', () => {
    it('next() loads next page with offset+1', () => {
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

      render(React.createElement(Fieldsets));

      mockDispatch.mockClear();

      const scrollProps = getInfiniteScrollProps();
      scrollProps.next();

      expect(mockDispatch).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(loadFieldsets({ offset: 3 }));
    });
  });

  describe('Sorting change', () => {
    it('reloads list when sorting changes', () => {
      const { rerender } = render(React.createElement(Fieldsets));

      expect(mockDispatch).toHaveBeenCalledWith(loadFieldsets({ offset: 0 }));
      mockDispatch.mockClear();
      (loadFieldsets as unknown as jest.Mock).mockClear();

      const newSortingState = {
        fieldsets: {
          ...defaultState.fieldsets,
          fieldsetsListSorting: EFieldsetsSorting.NameAsc,
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(newSortingState));

      rerender(React.createElement(Fieldsets));

      expect(mockDispatch).toHaveBeenCalledWith(loadFieldsets({ offset: 0 }));
    });
  });
});
