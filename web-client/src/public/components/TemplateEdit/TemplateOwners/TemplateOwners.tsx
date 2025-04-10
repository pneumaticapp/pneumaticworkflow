import React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { IApplicationState } from '../../../types/redux';
import { ESubscriptionPlan } from '../../../types/account';
import { createOwnerApiName } from '../../../utils/createId';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { getNotDeletedUsers, getUserFullName } from '../../../utils/users';
import { EOptionTypes, TUsersDropdownOption, UsersDropdown } from '../../UI/form/UsersDropdown';
import { getIsUserSubsribed, getSubscriptionPlan, getUsers } from '../../../redux/selectors/user';
import { ETaskPerformerType, ETemplateOwnerType, ITemplate, ITemplateOwner } from '../../../types/template';
import OwnerItem from './components';

import styles from './TemplateOwners.css';
import UserDataWithGroup from '../../UserDataWithGroup';

interface ITemplateOwnersProps {
  templateOwners: ITemplate['owners'];
  onChangeTemplateOwners(templateOwners: ITemplateOwner[]): void;
}

export function TemplateOwners({ templateOwners = [], onChangeTemplateOwners }: ITemplateOwnersProps) {
  const { formatMessage } = useIntl();

  const isSubscribed = useSelector(getIsUserSubsribed);
  const billingPlan = useSelector(getSubscriptionPlan);
  const groups = useSelector((state: IApplicationState) => state.groups.list);

  const users = getNotDeletedUsers(useSelector(getUsers));
  const mapUsersDropdownValue = users.filter((user) =>
    templateOwners.find(({ sourceId }) => Number(sourceId) === user.id),
  );

  const mapGroupDropdownValue = groups.filter((user) =>
    templateOwners.find(({ sourceId }) => Number(sourceId) === user.id),
  );

  const templateOwnerGroupDropdownOption = groups.map((group) => {
    return {
      ...group,
      optionType: EOptionTypes.Group,
      type: ETaskPerformerType.UserGroup,
      label: group.name,
      value: String(group.id),
    };
  });

  const templateOwnerDropdownOption = users.map((item) => {
    return {
      ...item,
      firstName: '',
      lastName: '',
      optionType: EOptionTypes.User,
      label: getUserFullName(item),
      value: String(item.id),
    };
  });

  const option = [
    ...templateOwnerGroupDropdownOption,
    ...templateOwnerDropdownOption,
  ] as unknown as TUsersDropdownOption[];

  const tplOwnerDropdownValueUsers = mapUsersDropdownValue.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.User,
      label: getUserFullName(item),
      value: String(item.id),
    };
  });

  const tplOwnerDropdownValueGroup = mapGroupDropdownValue.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.Group,
      label: item.name,
      value: String(item.id),
    };
  });

  const handleRemoveTemplateOwner = ({ id }: Pick<TUsersDropdownOption, 'id'>) => {
    const newTemplateOwners = templateOwners.filter(({ sourceId }) => sourceId !== String(id));
    onChangeTemplateOwners(newTemplateOwners);
  };

  const handleAddTemplateOwners = ({ id, optionType }: Pick<TUsersDropdownOption, 'id' | 'optionType'>) => {
    if (!isSubscribed && billingPlan !== ESubscriptionPlan.Free) return;
    const newOwner: ITemplateOwner = {
      sourceId: String(id),
      apiName: createOwnerApiName(),
      type: optionType as unknown as ETemplateOwnerType,
    };
    onChangeTemplateOwners([...templateOwners, newOwner]);
  };

  return (
    <>
      <UsersDropdown
        isMulti
        className={styles['dropdown']}
        placeholder={formatMessage({ id: 'user.search-field-placeholder' })}
        options={option}
        onChange={handleAddTemplateOwners}
        onChangeSelected={handleRemoveTemplateOwner}
        value={[...tplOwnerDropdownValueUsers, ...tplOwnerDropdownValueGroup]}
        onUsersInvited={({ id, optionType }) => handleAddTemplateOwners({ id, optionType })}
        onClickInvite={() => trackInviteTeamInPage('Template owners')}
        inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
      />
      <div className={styles['users']}>
        {templateOwners.map(({ sourceId, type }) => {
          return <UserDataWithGroup idItem={Number(sourceId)} type={type}>
            {(user) => {
              return (
                <OwnerItem
                  name={getUserFullName(user)}
                  user={user}
                  removeOwner={() => handleRemoveTemplateOwner({ id: Number(sourceId) })}
                />
              );
            }}
          </UserDataWithGroup>;
        })}
      </div>
    </>
  );
}
