import * as React from 'react';
import { ChangeEvent, ReactNode, useCallback } from 'react';
import classnames from 'classnames';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import { EOptionTypes, UsersDropdown } from '../../../UI/form/UsersDropdown';
import { getUsers } from '../../../../redux/selectors/user';
import { EUserDropdownOptionType, TUserListItem } from '../../../../types/user';
import { trackInviteTeamInPage } from '../../../../utils/analytics';
import { getInputNameBackground } from '../utils/getInputNameBackground';
import { ArrowDropdownIcon } from '../../../icons';
import { FieldWithName } from '../utils/FieldWithName';
import { getFieldValidator } from '../utils/getFieldValidator';
import { EExtraFieldMode, ETaskPerformerType } from '../../../../types/template';
import { isArrayWithItems } from '../../../../utils/helpers';
import { IWorkflowExtraFieldProps } from '..';
import { getNotDeletedUsers, getUserFullName } from '../../../../utils/users';
import { getRegularGroupsList } from '../../../../redux/selectors/groups';
import { IGroupDropdownOption } from '../../../../redux/team/types';

import styles from '../../KickoffRedux/KickoffRedux.css';
import inputStyles from './ExtraFieldUser.css';

export interface IExtraFieldUserProps extends IWorkflowExtraFieldProps {
  users: TUserListItem[];
}

export function ExtraFieldUser({
  field,
  field: { isRequired },
  intl,
  descriptionPlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }),
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  isDisabled = false,
  labelBackgroundColor,
  innerRef,
}: IExtraFieldUserProps) {
  const { formatMessage } = useIntl();

  const users: ReturnType<typeof getUsers> = getNotDeletedUsers(useSelector(getUsers));
  const groups = useSelector(getRegularGroupsList);

  const { description } = field;

  const fieldNameClassName = classnames(getInputNameBackground(labelBackgroundColor), styles['kick-off-input__name']);

  const handleChangeName = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      editField({ name: e.target.value });
    },
    [editField],
  );

  const handleChangeDescription = useCallback(
    (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      editField({ description: e.target.value });
    },
    [editField],
  );

  const renderKickoffField = () => (
    <FieldWithName
      inputClassName={inputStyles['kickoff-dropdown-field']}
      labelBackgroundColor={labelBackgroundColor}
      field={field}
      descriptionPlaceholder={descriptionPlaceholder}
      namePlaceholder={namePlaceholder}
      mode={mode}
      handleChangeName={handleChangeName}
      handleChangeDescription={handleChangeDescription}
      validate={getFieldValidator(field, mode)}
      isDisabled={isDisabled}
      icon={<ArrowDropdownIcon />}
      innerRef={innerRef}
    />
  );

  const renderKickoffView = () => (
    <div className={inputStyles['kickoff-create-field-container']}>{renderKickoffField()}</div>
  );

  const renderSelectableView = () => {
    const usersDropdownOption = users.map((item) => {
      return {
        ...item,
        optionType: EOptionTypes.User,
        label: getUserFullName(item),
        value: `${EOptionTypes.User}-${item.id}`,
      };
    });
    const groupsDropdownOption = groups.map((item) => {
      return {
        ...item,
        optionType: EOptionTypes.Group,
        label: item.name,
        value: `${EOptionTypes.Group}-${item.id}`,
        type: ETaskPerformerType.UserGroup,
      };
    });
    const selectionsDropdownOption = [...groupsDropdownOption, ...usersDropdownOption];

    const onUsersInvited = (invitedUsers: TUserListItem[]) => {
      if (!isArrayWithItems(invitedUsers)) return;

      const value = invitedUsers[0] && String(invitedUsers[0].id);
      editField({ value });
    };

    const handleUserDropdownChange = (option: TUserListItem | IGroupDropdownOption) => {
      if (option.type === EUserDropdownOptionType.User) {
        const user = option as TUserListItem;
        editField({ value: user.email, userId: user.id, groupId: null });
        return;
      }
      if (option.type === EUserDropdownOptionType.UserGroup) {
        const group = option as IGroupDropdownOption;
        editField({ value: group.name, groupId: option.id, userId: null });
      }
    };

    return (
      <div className={classnames(inputStyles['dropdown-container'])} data-autofocus-first-field>
        <div className={fieldNameClassName}>
          <div className={styles['kick-off-input__name-readonly']}>{field.name}</div>
          {isRequired && <span className={styles['kick-off-required-sign']} />}
        </div>
        <UsersDropdown
          options={selectionsDropdownOption}
          onChange={handleUserDropdownChange}
          placeholder={description}
          isDisabled={isDisabled}
          value={selectionsDropdownOption.find(
            (item) =>
              item.value === `${EOptionTypes.User}-${field.userId}` ||
              item.value === `${EOptionTypes.Group}-${field.groupId}`,
          )}
          onClickInvite={() => trackInviteTeamInPage('From users field')}
          inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
          onUsersInvited={onUsersInvited}
        />
      </div>
    );
  };

  const renderDropdownField = () => {
    const fieldsMap: { [key in EExtraFieldMode]: ReactNode } = {
      [EExtraFieldMode.Kickoff]: renderKickoffView(),
      [EExtraFieldMode.ProcessRun]: renderSelectableView(),
    };

    return fieldsMap[mode];
  };

  return <>{renderDropdownField()}</>;
}
