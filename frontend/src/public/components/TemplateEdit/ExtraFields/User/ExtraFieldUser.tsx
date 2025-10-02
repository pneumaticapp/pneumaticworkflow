import React, { ChangeEvent, ReactNode, useCallback, useEffect, useRef } from 'react';
import classnames from 'classnames';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import AutosizeInput from 'react-input-autosize';

import { EOptionTypes, TUsersDropdownOption, UsersDropdown } from '../../../UI/form/UsersDropdown';
import { getUsers } from '../../../../redux/selectors/user';
import { TUserListItem } from '../../../../types/user';
import { trackInviteTeamInPage } from '../../../../utils/analytics';
import { fitInputWidth } from '../utils/fitInputWidth';
import { getInputNameBackground } from '../utils/getInputNameBackground';
import { ArrowDropdownIcon } from '../../../icons';
import { FieldWithName } from '../utils/FieldWithName';
import { getFieldValidator } from '../utils/getFieldValidator';
import { EExtraFieldMode } from '../../../../types/template';
import { isArrayWithItems } from '../../../../utils/helpers';
import { IWorkflowExtraFieldProps } from '..';
import { getNotDeletedUsers, getUserFullName } from '../../../../utils/users';

import styles from '../../KickoffRedux/KickoffRedux.css';
import inputStyles from './ExtraFieldUser.css';

const DEFAULT_FIELD_INPUT_WIDTH = 120;

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

  const fieldNameInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const initialSelection = field.selections?.find((selection) => selection.isSelected)?.id;
    const shouldSetInitialValue = Number.isFinite(initialSelection) && mode === EExtraFieldMode.ProcessRun;

    if (shouldSetInitialValue) {
      editField({ value: String(initialSelection) });
    }

    fitInputWidth(fieldNameInputRef.current, DEFAULT_FIELD_INPUT_WIDTH);
  }, []);

  const { description } = field;

  const fieldNameClassName = classnames(getInputNameBackground(labelBackgroundColor), styles['kick-off-input__name']);

  const handleChangeName = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      fitInputWidth(e.target, DEFAULT_FIELD_INPUT_WIDTH);
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
    const users: ReturnType<typeof getUsers> = getNotDeletedUsers(useSelector(getUsers));
    const selectionsDropdownOption = users.map((item) => {
      return {
        ...item,
        optionType: EOptionTypes.User,
        label: getUserFullName(item),
        value: String(item.id),
      };
    });

    const onUsersInvited = (invitedUsers: TUserListItem[]) => {
      if (!isArrayWithItems(invitedUsers)) return;

      const value = invitedUsers[0] && String(invitedUsers[0].id);
      editField({ value });
    };

    const handleUserDropdownChange = ({ id }: TUsersDropdownOption) => {
      editField({ value: String(id) });
    };

    return (
      <div className={classnames(inputStyles['dropdown-container'])} data-autofocus-first-field>
        <UsersDropdown
          options={selectionsDropdownOption}
          onChange={handleUserDropdownChange}
          placeholder={description}
          isDisabled={isDisabled}
          value={selectionsDropdownOption.find((item) => item.value === field.value)}
          onClickInvite={() => trackInviteTeamInPage('From users field')}
          inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
          onUsersInvited={onUsersInvited}
        />
        <div className={fieldNameClassName}>
          <AutosizeInput
            inputRef={(ref) => {
              fieldNameInputRef.current = ref;
            }}
            inputClassName={inputStyles['kickoff-create-field-name-input']}
            disabled={mode !== EExtraFieldMode.Kickoff || isDisabled}
            onChange={handleChangeName}
            placeholder={namePlaceholder}
            type="text"
            value={field.name}
          />
          {isRequired && <span className={styles['kick-off-required-sign']} />}
        </div>
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

  return renderDropdownField();
}
