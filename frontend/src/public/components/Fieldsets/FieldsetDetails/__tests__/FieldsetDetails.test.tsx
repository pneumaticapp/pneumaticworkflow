// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import FieldsetDetails from '../FieldsetDetails';
import { history } from '../../../../utils/history';
import { ERoutes } from '../../../../constants/routes';
import {
  loadCurrentFieldset,
  setTemplateId,
  resetCurrentFieldset,
} from '../../../../redux/fieldsets/slice';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../../redux/fieldsets/slice', () => ({
  openEditModal: jest.fn(() => ({ type: 'fieldsets/openEditModal' })),
  deleteFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/deleteFieldsetAction', payload: p })),
  loadCurrentFieldset: jest.fn((p) => ({ type: 'fieldsets/loadCurrentFieldset', payload: p })),
  resetCurrentFieldset: jest.fn(() => ({ type: 'fieldsets/resetCurrentFieldset' })),
  updateFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/updateFieldsetAction', payload: p })),
  setTemplateId: jest.fn((p) => ({ type: 'fieldsets/setTemplateId', payload: p })),
}));

jest.mock('../../../UI', () => ({
  ModifyDropdown: jest.fn(() => null),
  Button: jest.fn(() => null),
  FilterSelect: jest.fn(() => null),
}));

jest.mock('../../../UI/ModifyDropdown/types', () => ({
  EModifyDropdownToggle: { Modify: 'modify' },
}));

jest.mock('../../FieldsetModal/FieldsetModal', () => ({
  FieldsetModal: jest.fn(() => null),
}));

jest.mock('../../FieldsetModal/types', () => ({
  EFieldsetModalType: { Edit: 'edit' },
}));

jest.mock('../FieldsetDetailsSkeleton', () => ({
  FieldsetDetailsSkeleton: jest.fn(() =>
    React.createElement('div', { 'data-testid': 'skeleton' }),
  ),
}));

jest.mock('../../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn(() => null),
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/ExtraFieldsMap', () => ({
  ExtraFieldsMap: [],
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/ExtraFieldIcon', () => ({
  ExtraFieldIcon: jest.fn(() => null),
}));

jest.mock('../../../TemplateEdit/KickoffRedux/utils/getEmptyField', () => ({
  getEmptyField: jest.fn(),
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/getEditedFields', () => ({
  getEditedFields: jest.fn(),
}));

jest.mock('../../../../utils/workflows', () => ({
  getNormalizeFieldsOrders: jest.fn((f) => f),
  moveWorkflowField: jest.fn(),
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/useDatasetOptions', () => ({
  useDatasetOptions: jest.fn(() => []),
}));

jest.mock('../fieldsetFieldMappers', () => ({
  normalizeFieldsForUI: jest.fn((f) => f),
}));

describe('FieldsetDetails', () => {
  const mockDispatch = jest.fn();

  const makeProps = (id: string = '10', templateId: string = '5') => ({
    match: { params: { id, templateId }, isExact: true, path: '', url: '' },
    location: {
      pathname: `/templates/${templateId}/fieldsets/${id}/`,
      search: '',
      hash: '',
      state: undefined,
    },
    history: history as any,
  });

  const loadingState = {
    fieldsets: {
      currentFieldset: null,
      isCurrentFieldsetLoading: true,
    },
    authUser: { account: { id: 1 } },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockImplementation((selector) => selector(loadingState));
  });

  describe('URL parameter validation', () => {
    it('redirects to /templates/ when templateId is NaN', () => {
      render(React.createElement(FieldsetDetails, makeProps('10', 'abc')));

      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(ERoutes.Templates);
      expect(setTemplateId).not.toHaveBeenCalled();
      expect(loadCurrentFieldset).not.toHaveBeenCalled();
    });

    it('redirects to fieldset list when id is NaN', () => {
      render(React.createElement(FieldsetDetails, makeProps('xyz', '5')));

      const expectedRoute = ERoutes.TemplateFieldsets.replace(':templateId', '5');
      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(expectedRoute);
    });

    it('dispatches setTemplateId and loadCurrentFieldset when both params are valid', () => {
      render(React.createElement(FieldsetDetails, makeProps('10', '5')));

      expect(history.push).not.toHaveBeenCalled();
      expect(mockDispatch).toHaveBeenCalledWith(setTemplateId(5));
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
});
