// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';
import { useSelector } from 'react-redux';

import { ExtraFieldUser, IExtraFieldUserProps } from '../ExtraFieldUser';
import { EExtraFieldMode, EExtraFieldType } from '../../../../../types/template';
import { EUserDropdownOptionType } from '../../../../../types/user';
import { UsersDropdown } from '../../../../UI/form/UsersDropdown';

jest.mock('react-redux', () => ({
  useSelector: jest.fn(),
  useDispatch: jest.fn(),
}));

jest.mock('react-intl', () => ({
  useIntl: () => ({ formatMessage: ({ id }: { id: string }) => id }),
}));

jest.mock('../../../../UI/form/UsersDropdown', () => ({
  UsersDropdown: jest.fn(() => null),
  EOptionTypes: { User: 'user', Group: 'group' },
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
  getUserFullName: jest.fn((user) => `User ${user.id}`),
}));

jest.mock('../../../../../utils/analytics', () => ({
  trackInviteTeamInPage: jest.fn(),
}));

describe('ExtraFieldUser', () => {
  const mockEditField = jest.fn();

  const mockUsers = [{ id: 1, firstName: 'User1', email: 'user1@test.com' }];
  const mockGroups = [{ id: 1, name: 'Group1' }];

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector) => {
      if (typeof selector === 'function' && selector.name === 'getGroupsList') return mockGroups;
      return mockUsers;
    });
  });

  const getDropdownProps = (): any => {
    const mock = UsersDropdown as unknown as jest.Mock;
    if (!mock.mock.calls.length) return null;
    return mock.mock.calls[mock.mock.calls.length - 1][0];
  };

  const createBaseField = (overrides = {}) => ({
    apiName: 'field-1',
    name: 'User Field',
    description: '',
    type: EExtraFieldType.User,
    userId: null,
    groupId: null,
    isRequired: false,
    ...overrides,
  });

  describe('Value matching logic', () => {
    it('selects user option when field.userId matches and field.groupId is null, avoiding group ID collisions', () => {
      render(
        React.createElement(ExtraFieldUser, {
          field: createBaseField({ userId: 1 }),
          mode: EExtraFieldMode.ProcessRun,
          editField: mockEditField,
          users: mockUsers,
          intl: { formatMessage: () => '' },
        } as unknown as IExtraFieldUserProps)
      );

      const props = getDropdownProps();
      expect(props.value).toBeDefined();
      expect(props.value.value).toBe('user-1');
      expect(props.value.optionType).toBe('user');
    });

    it('selects group option when field.groupId matches and field.userId is null, avoiding user ID collisions', () => {
      render(
        React.createElement(ExtraFieldUser, {
          field: createBaseField({ groupId: 1 }),
          mode: EExtraFieldMode.ProcessRun,
          editField: mockEditField,
          users: mockUsers,
          intl: { formatMessage: () => '' },
        } as unknown as IExtraFieldUserProps)
      );

      const props = getDropdownProps();
      expect(props.value).toBeDefined();
      expect(props.value.value).toBe('group-1');
      expect(props.value.optionType).toBe('group');
    });

    it('returns undefined value when neither userId nor groupId are set', () => {
      render(
        React.createElement(ExtraFieldUser, {
          field: createBaseField(),
          mode: EExtraFieldMode.ProcessRun,
          editField: mockEditField,
          users: mockUsers,
          intl: { formatMessage: () => '' },
        } as unknown as IExtraFieldUserProps)
      );

      const props = getDropdownProps();
      expect(props.value).toBeUndefined();
    });
  });

  describe('Selection handling', () => {
    it('sets userId and clears groupId when a user is selected from dropdown', () => {
      render(
        React.createElement(ExtraFieldUser, {
          field: createBaseField(),
          mode: EExtraFieldMode.ProcessRun,
          editField: mockEditField,
          users: mockUsers,
          intl: { formatMessage: () => '' },
        } as unknown as IExtraFieldUserProps)
      );

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
      render(
        React.createElement(ExtraFieldUser, {
          field: createBaseField(),
          mode: EExtraFieldMode.ProcessRun,
          editField: mockEditField,
          users: mockUsers,
          intl: { formatMessage: () => '' },
        } as unknown as IExtraFieldUserProps)
      );

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
});
