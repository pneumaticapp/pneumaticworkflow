import * as React from 'react';
import { render } from '@testing-library/react';
import { useSelector } from 'react-redux';
import { Location } from 'history';

import { FieldsetUnsavedChangesModal } from '../FieldsetUnsavedChangesModal';
import { RouteLeavingGuard } from '../../../UI';
import { makeFieldsetCatalogItem } from '../../../../__stubs__/fieldsets.factory';
import { intlMock } from '../../../../__stubs__/intlMock';
import { history } from '../../../../utils/history';
import { ERoutes } from '../../../../constants/routes';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn() },
}));

jest.mock('../../../UI', () => ({
  Button: jest.fn((props: { label: string; onClick?: () => void }) =>
    React.createElement('button', { onClick: props.onClick }, props.label),
  ),
  RouteLeavingGuard: jest.fn(() => null),
}));

type TRouteLeavingGuardProps = {
  when: boolean;
  title: string;
  shouldBlockNavigation: (location: Location) => boolean;
  onConfirm: (path: string) => void;
};

describe('FieldsetUnsavedChangesModal', () => {
  const formatMsg = (id: string, values?: Record<string, string>) =>
    intlMock.formatMessage({ id }, values);
  const fieldset = makeFieldsetCatalogItem({ id: 10, name: 'My Fieldset' });
  const detailPath = ERoutes.FieldsetDetail.replace(':id', String(fieldset.id));

  const mockState = {
    fieldsets: { currentFieldset: fieldset },
  };

  const getGuardProps = (): TRouteLeavingGuardProps => {
    if (!jest.isMockFunction(RouteLeavingGuard)) {
      throw new Error('RouteLeavingGuard is not a jest.Mock');
    }
    const firstCall = RouteLeavingGuard.mock.calls[0];
    if (!firstCall) {
      throw new Error('RouteLeavingGuard was not called');
    }
    return firstCall[0] as TRouteLeavingGuardProps;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector: (state: object) => unknown) =>
      selector(mockState),
    );
  });

  it('does not render guard when currentFieldset is null', () => {
    const emptyState = { fieldsets: { currentFieldset: null } };
    (useSelector as jest.Mock).mockImplementation((selector: (state: object) => unknown) =>
      selector(emptyState),
    );

    const { container } = render(
      React.createElement(FieldsetUnsavedChangesModal, { isChanged: true, onSave: jest.fn() }),
    );

    expect(container).toBeEmptyDOMElement();
    expect(RouteLeavingGuard).not.toHaveBeenCalled();
  });

  it('passes when=false to RouteLeavingGuard when there are no changes', () => {
    render(React.createElement(FieldsetUnsavedChangesModal, { isChanged: false, onSave: jest.fn() }));

    expect(RouteLeavingGuard).toHaveBeenCalledTimes(1);
    expect(RouteLeavingGuard).toHaveBeenCalledWith(
      expect.objectContaining({
        when: false,
        title: formatMsg('fieldsets.leave-unsaved-title', { name: fieldset.name }),
      }),
      {},
    );
  });

  it('passes when=true to RouteLeavingGuard when there are unsaved changes', () => {
    render(React.createElement(FieldsetUnsavedChangesModal, { isChanged: true, onSave: jest.fn() }));

    expect(RouteLeavingGuard).toHaveBeenCalledTimes(1);
    expect(RouteLeavingGuard).toHaveBeenCalledWith(
      expect.objectContaining({ when: true }),
      {},
    );
  });

  it('shouldBlockNavigation returns false for the same detail path', () => {
    render(React.createElement(FieldsetUnsavedChangesModal, { isChanged: true, onSave: jest.fn() }));

    const { shouldBlockNavigation } = getGuardProps();

    expect(shouldBlockNavigation({ pathname: detailPath } as Location)).toBe(false);
  });

  it('shouldBlockNavigation returns true for another path', () => {
    render(React.createElement(FieldsetUnsavedChangesModal, { isChanged: true, onSave: jest.fn() }));

    const { shouldBlockNavigation } = getGuardProps();

    expect(shouldBlockNavigation({ pathname: ERoutes.Fieldsets } as Location)).toBe(true);
  });

  it('onConfirm calls history.push with the given path', () => {
    render(React.createElement(FieldsetUnsavedChangesModal, { isChanged: true, onSave: jest.fn() }));

    const { onConfirm } = getGuardProps();
    onConfirm('/fieldsets/');

    expect(history.push).toHaveBeenCalledTimes(1);
    expect(history.push).toHaveBeenCalledWith('/fieldsets/');
  });

  describe('Conditional navigation on Save button click in modal', () => {
    it('passes onSave handler to modal options', () => {
      const onSaveMock = jest.fn().mockReturnValue(true);
      render(React.createElement(FieldsetUnsavedChangesModal, { isChanged: true, onSave: onSaveMock }));

      expect(RouteLeavingGuard).toHaveBeenCalledTimes(1);
    });

    it('calls confirmLeave when onSave handler returns true', () => {
      const onSaveMock = jest.fn().mockReturnValue(true);
      render(React.createElement(FieldsetUnsavedChangesModal, { isChanged: true, onSave: onSaveMock }));

      const renderControlls = (RouteLeavingGuard as jest.Mock).mock.calls[0][0].renderControlls;
      const confirmLeaveMock = jest.fn();
      const stayMock = jest.fn();

      const controls = render(renderControlls(confirmLeaveMock, stayMock));
      const saveButton = controls.getByText(formatMsg('fieldsets.leave-unsaved-save'));

      saveButton.click();

      expect(onSaveMock).toHaveBeenCalledTimes(1);
      expect(confirmLeaveMock).toHaveBeenCalledTimes(1);
    });

    it('calls stay() and does not call confirmLeave when onSave returns false', () => {
      const onSaveMock = jest.fn().mockReturnValue(false);
      render(React.createElement(FieldsetUnsavedChangesModal, { isChanged: true, onSave: onSaveMock }));

      const renderControlls = (RouteLeavingGuard as jest.Mock).mock.calls[0][0].renderControlls;
      const confirmLeaveMock = jest.fn();
      const stayMock = jest.fn();

      const controls = render(renderControlls(confirmLeaveMock, stayMock));
      const saveButton = controls.getByText(formatMsg('fieldsets.leave-unsaved-save'));

      saveButton.click();

      expect(onSaveMock).toHaveBeenCalledTimes(1);
      expect(confirmLeaveMock).not.toHaveBeenCalled();
      expect(stayMock).toHaveBeenCalledTimes(1);
    });
  });
});
