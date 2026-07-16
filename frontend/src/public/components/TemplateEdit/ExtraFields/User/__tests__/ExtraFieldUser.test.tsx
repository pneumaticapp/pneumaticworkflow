import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useSelector } from 'react-redux';

import { ExtraFieldUser, IExtraFieldUserProps } from '../ExtraFieldUser';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EExtraFieldMode, EExtraFieldType } from '../../../../../types/template';
import { EUserDropdownOptionType, TUserListItem, EUserStatus } from '../../../../../types/user';

import { FieldLabel } from '../../utils/FieldLabel';
import { EFieldLabelPosition } from '../../../../../types/fieldset';

jest.mock('react-redux', () => ({
  useSelector: jest.fn(),
  useDispatch: jest.fn(),
}));

jest.mock('react-intl', () => ({
  ...jest.requireActual('react-intl'),
  useIntl: () => ({ formatMessage: ({ id }: { id: string }) => id }),
}));

jest.mock('../../../../UI/form/UsersDropdown', () => ({
  UsersDropdown: jest.fn(() => null),
  EOptionTypes: { User: 'user', Group: 'group' },
  getUsersDropdownOptionValue: (optionType: string, id: number | string) => `${optionType}-${id}`,
}));

jest.mock('../../utils/FieldWithName', () => ({
  FieldWithName: () => null,
}));

jest.mock('react-input-autosize', () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock('../../../../../utils/users', () => ({
  getNotDeletedUsers: jest.fn((users) => users),
  getUserFullName: jest.fn((user: { id: number }) => `User ${user.id}`),
}));

jest.mock('../../../../../utils/analytics', () => ({
  trackInviteTeamInPage: jest.fn(),
}));

jest.mock('../../utils/FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

describe('ExtraFieldUser', () => {
  const mockEditField = jest.fn();

  const mockUsers: TUserListItem[] = [{
    id: 1,
    firstName: 'User1',
    lastName: '',
    email: 'user1@test.com',
    phone: '',
    photo: '',
    type: 'user',
    status: EUserStatus.Active,
    isAdmin: false,
    isAccountOwner: false,
  }];
  const mockGroups = [{ id: 1, name: 'Group1' }];

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector) => {
      if (typeof selector === 'function' && selector.name === 'getRegularGroupsList') return mockGroups;
      return mockUsers;
    });
  });

  const getDropdownProps = () => {
    const { UsersDropdown: mock } = require('../../../../UI/form/UsersDropdown');
    if (!mock.mock.calls.length) return null;
    return mock.mock.calls[mock.mock.calls.length - 1][0];
  };

  const createBaseField = (overrides = {}) => makeExtraField({
    name: 'User Field',
    type: EExtraFieldType.User,
    ...overrides,
  });

  const baseProps: IExtraFieldUserProps = {
    field: createBaseField(),
    mode: EExtraFieldMode.ProcessRun,
    editField: mockEditField,
    users: mockUsers,
    intl: intlMock,
    accountId: 1,
    labelPosition: EFieldLabelPosition.Top,
  };

  describe('Value matching logic', () => {
    it('selects user option when field.userId matches and field.groupId is null, avoiding group ID collisions', () => {
      render(<ExtraFieldUser {...baseProps} field={createBaseField({ userId: 1 })} />);

      const props = getDropdownProps();
      expect(props.value).toBeDefined();
      expect(props.value.value).toBe('user-1');
      expect(props.value.optionType).toBe('user');
    });

    it('selects group option when field.groupId matches and field.userId is null, avoiding user ID collisions', () => {
      render(<ExtraFieldUser {...baseProps} field={createBaseField({ groupId: 1 })} />);

      const props = getDropdownProps();
      expect(props.value).toBeDefined();
      expect(props.value.value).toBe('group-1');
      expect(props.value.optionType).toBe('group');
    });

    it('returns undefined value when neither userId nor groupId are set', () => {
      render(<ExtraFieldUser {...baseProps} />);

      const props = getDropdownProps();
      expect(props.value).toBeUndefined();
    });
  });

  describe('Selection handling', () => {
    it('sets userId and clears groupId when a user is selected from dropdown', () => {
      render(<ExtraFieldUser {...baseProps} />);

      const props = getDropdownProps();
      props.onChange({
        type: EUserDropdownOptionType.User,
        id: 1,
        email: 'user1@test.com',
      });

      expect(mockEditField).toHaveBeenCalledWith({
        value: 'user1@test.com',
        userId: 1,
        groupId: null,
      });
    });

    it('sets groupId and clears userId when a group is selected from dropdown', () => {
      render(<ExtraFieldUser {...baseProps} />);

      const props = getDropdownProps();
      props.onChange({
        type: EUserDropdownOptionType.UserGroup,
        id: 1,
        name: 'Group1',
      });

      expect(mockEditField).toHaveBeenCalledWith({
        value: 'Group1',
        groupId: 1,
        userId: null,
      });
    });
  });

  describe('label-left support', () => {
    it('ProcessRun + labelPosition=Left: renders FieldLabel with centered class', () => {
      render(<ExtraFieldUser {...baseProps} labelPosition={EFieldLabelPosition.Left} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalledTimes(1);
      expect(fieldLabelMock).toHaveBeenCalledWith(
        expect.objectContaining({
          className: expect.stringContaining('centered'),
        }),
        {},
      );
    });

    it('ProcessRun + labelPosition=Top: renders static name div, no FieldLabel', () => {
      render(<ExtraFieldUser {...baseProps} labelPosition={EFieldLabelPosition.Top} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
      expect(screen.getByText('User Field')).toBeInTheDocument();
    });
  });
});
