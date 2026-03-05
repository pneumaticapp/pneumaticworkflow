import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { ExtraFieldDropdown } from '../ExtraFieldDropdown';
import { enMessages } from '../../../../../lang/locales/en_US';

jest.mock('react-outside-click-handler', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const baseProps = {
  isRequired: false,
  isRequiredDisabled: false,
  isHidden: false,
  onEditField: jest.fn(),
  onDeleteField: jest.fn(),
  onMoveFieldUp: jest.fn(),
  onMoveFieldDown: jest.fn(),
};

const renderWithIntl = (ui: React.ReactElement) =>
  render(<IntlProvider locale="en" messages={enMessages}>{ui}</IntlProvider>);

describe('ExtraFieldDropdown', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const getRequiredSwitch = () => screen.getByRole('switch', { name: 'Required', hidden: true });
  const getHiddenSwitch = () => screen.getByRole('switch', { name: 'Hidden', hidden: true });

  describe('Render', () => {
    it('renders Hidden switch', () => {
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isHidden={false} />);

      expect(getHiddenSwitch()).toBeInTheDocument();
    });
  });

  describe('Required / Hidden mutual exclusion', () => {
    it('Required switch is disabled when field is hidden', () => {
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isHidden={true} />);

      expect(getRequiredSwitch()).toBeDisabled();
    });

    it('Hidden switch is disabled when field is required', () => {
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isRequired={true} />);

      expect(getHiddenSwitch()).toBeDisabled();
    });

    it('Required switch is disabled when isRequiredDisabled', () => {
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isRequiredDisabled={true} />);

      expect(getRequiredSwitch()).toBeDisabled();
    });
  });

  describe('Callbacks', () => {
    it('toggling Hidden on calls onEditField with isHidden=true', () => {
      const onEditField = jest.fn();
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isHidden={false} onEditField={onEditField} />);

      userEvent.click(getHiddenSwitch());

      expect(onEditField).toHaveBeenCalledTimes(1);
      expect(onEditField).toHaveBeenCalledWith({ isHidden: true });
    });

    it('toggling Hidden off calls onEditField with isHidden=false', () => {
      const onEditField = jest.fn();
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isHidden={true} onEditField={onEditField} />);

      userEvent.click(getHiddenSwitch());

      expect(onEditField).toHaveBeenCalledTimes(1);
      expect(onEditField).toHaveBeenCalledWith({ isHidden: false });
    });
  });
});
