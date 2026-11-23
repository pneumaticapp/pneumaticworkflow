import React from 'react';
import { render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import FieldsetDetails from '../FieldsetDetails';
import { FieldsetDetailsForm } from '../FieldsetDetailsForm';
import { history } from '../../../../utils/history';
import { ERoutes } from '../../../../constants/routes';
import type { TFieldsetDetailsProps } from '../types';
import { loadCurrentFieldset, resetCurrentFieldset } from '../../../../redux/fieldsets/slice';
import { makeFieldsetCatalogItem } from '../../../../__stubs__/fieldsets.factory';
import type { RootState } from '../../../../redux/store';

jest.mock('../../../../utils/history', () => ({
  history: {
    push: jest.fn(),
    location: { pathname: '/' },
    listen: jest.fn(),
    length: 1,
    action: 'PUSH',
    go: jest.fn(),
    goBack: jest.fn(),
    goForward: jest.fn(),
    replace: jest.fn(),
    block: jest.fn(),
    createHref: jest.fn(),
  },
}));

jest.mock('../../../../redux/fieldsets/slice', () => ({
  loadCurrentFieldset: jest.fn((payload) => ({ type: 'fieldsets/loadCurrentFieldset', payload })),
  resetCurrentFieldset: jest.fn(() => ({ type: 'fieldsets/resetCurrentFieldset' })),
}));

jest.mock('../FieldsetDetailsSkeleton', () => ({
  FieldsetDetailsSkeleton: jest.fn(() => React.createElement('div', { role: 'status', 'aria-label': 'Loading' })),
}));

jest.mock('../FieldsetDetailsForm', () => ({
  FieldsetDetailsForm: jest.fn(() => null),
}));

describe('FieldsetDetails', () => {
  const mockDispatch = jest.fn();

  const makeProps = (id: string = '10'): TFieldsetDetailsProps => ({
    match: { params: { id }, isExact: true, path: '', url: '' },
    location: { pathname: `/fieldsets/${id}/`, search: '', hash: '', state: undefined },
    history,
  });

  const loadingState: Pick<RootState, 'fieldsets'> = {
    fieldsets: { currentFieldset: null, isCurrentFieldsetLoading: true } as RootState['fieldsets'],
  };

  const nullFieldsetState: Pick<RootState, 'fieldsets'> = {
    fieldsets: { currentFieldset: null, isCurrentFieldsetLoading: false } as RootState['fieldsets'],
  };

  const makeLoadedState = (fieldsetOverrides = {}): Pick<RootState, 'fieldsets'> => {
    const fieldset = makeFieldsetCatalogItem({
      id: 10,
      layout: 'horizontal',
      ...fieldsetOverrides,
    });
    return {
      fieldsets: { currentFieldset: fieldset, isCurrentFieldsetLoading: false } as RootState['fieldsets'],
    };
  };

  const mockSelectorState = (state: Pick<RootState, 'fieldsets'>) => {
    (useSelector as jest.Mock).mockImplementation((selector: (storeState: Pick<RootState, 'fieldsets'>) => unknown) =>
      selector(state),
    );
  };

  const renderWithState = (state: Pick<RootState, 'fieldsets'>, properties = makeProps()) => {
    mockSelectorState(state);
    return render(React.createElement(FieldsetDetails, properties));
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    mockSelectorState(loadingState);
  });

  describe('URL parameter validation', () => {
    it('redirects to fieldsets list on invalid id', () => {
      render(React.createElement(FieldsetDetails, makeProps('xyz')));
      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(ERoutes.Fieldsets);
    });

    it('dispatches loadCurrentFieldset on valid params', () => {
      render(React.createElement(FieldsetDetails, makeProps('10')));
      expect(history.push).not.toHaveBeenCalled();
      expect(mockDispatch).toHaveBeenCalledWith(loadCurrentFieldset({ id: 10 }));
    });
  });

  it('dispatches resetCurrentFieldset on unmount', () => {
    const { unmount } = render(React.createElement(FieldsetDetails, makeProps()));
    mockDispatch.mockClear();
    unmount();
    expect(mockDispatch).toHaveBeenCalledTimes(1);
    expect(mockDispatch).toHaveBeenCalledWith(resetCurrentFieldset());
  });

  it('skips loadCurrentFieldset when fieldset is already loaded with same id', () => {
    renderWithState(makeLoadedState({ id: 10 }), makeProps('10'));
    expect(loadCurrentFieldset).not.toHaveBeenCalled();
  });

  describe('Loading state', () => {
    it('renders Skeleton when isLoading=true', () => {
      renderWithState(loadingState);
      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(FieldsetDetailsForm).not.toHaveBeenCalled();
    });

    it('renders nothing when fieldset=null and isLoading=false', () => {
      const { container } = renderWithState(nullFieldsetState);
      expect(container).toBeEmptyDOMElement();
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
      expect(FieldsetDetailsForm).not.toHaveBeenCalled();
    });

    it('mounts FieldsetDetailsForm with loaded fieldset after loading completes', () => {
      mockSelectorState(loadingState);
      const { rerender } = render(React.createElement(FieldsetDetails, makeProps('10')));

      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(FieldsetDetailsForm).not.toHaveBeenCalled();

      const loadedState = makeLoadedState({ id: 10, title: 'Loaded Title' });
      mockSelectorState(loadedState);
      rerender(React.createElement(FieldsetDetails, makeProps('10')));

      expect(FieldsetDetailsForm).toHaveBeenCalledTimes(1);
      expect(FieldsetDetailsForm).toHaveBeenCalledWith(
        expect.objectContaining({ fieldset: loadedState.fieldsets.currentFieldset }),
        {},
      );
    });
  });
});
