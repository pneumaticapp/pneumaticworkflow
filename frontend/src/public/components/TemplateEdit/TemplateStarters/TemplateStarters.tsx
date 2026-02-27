import React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { IApplicationState } from '../../../types/redux';
import { ESubscriptionPlan } from '../../../types/account';
import { createStarterApiName } from '../../../utils/createId';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { getNotDeletedUsers, getUserFullName } from '../../../utils/users';
import { EOptionTypes, TUsersDropdownOption, UsersDropdown } from '../../UI/form/UsersDropdown';
import { getIsUserSubsribed, getSubscriptionPlan, getUsers } from '../../../redux/selectors/user';
import { ETaskPerformerType, ETemplateOwnerType, ETemplateStarterType, ITemplate, ITemplateStarter } from '../../../types/template';
import StarterItem from './components';

import styles from './TemplateStarters.css';
import UserDataWithGroup from '../../UserDataWithGroup';

interface ITemplateStartersProps {
  templateStarters: ITemplate['starters'];
  onChangeTemplateStarters(templateStarters: ITemplateStarter[]): void;
}

export function TemplateStarters({ templateStarters = [], onChangeTemplateStarters }: ITemplateStartersProps) {
  const { formatMessage } = useIntl();

  const isSubscribed = useSelector(getIsUserSubsribed);
  const billingPlan = useSelector(getSubscriptionPlan);
  const groups = useSelector((state: IApplicationState) => state.groups.list);

  const users = getNotDeletedUsers(useSelector(getUsers));
  const mapUsersDropdownValue = users.filter((user) =>
    templateStarters.find(({ sourceId }) => Number(sourceId) === user.id),
  );

  const mapGroupDropdownValue = groups.filter((group) =>
    templateStarters.find(({ sourceId }) => Number(sourceId) === group.id),
  );

  const templateStarterGroupDropdownOption = groups.map((group) => {
    return {
      ...group,
      optionType: EOptionTypes.Group,
      type: ETaskPerformerType.UserGroup,
      label: group.name,
      value: String(group.id),
    };
  });

  const templateStarterDropdownOption = users.map((item) => {
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
    ...templateStarterGroupDropdownOption,
    ...templateStarterDropdownOption,
  ] as unknown as TUsersDropdownOption[];

  const tplStarterDropdownValueUsers = mapUsersDropdownValue.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.User,
      label: getUserFullName(item),
      value: String(item.id),
    };
  });

  const tplStarterDropdownValueGroup = mapGroupDropdownValue.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.Group,
      label: item.name,
      value: String(item.id),
    };
  });

  const handleRemoveTemplateStarter = ({ id }: Pick<TUsersDropdownOption, 'id'>) => {
    const newTemplateStarters = templateStarters.filter(({ sourceId }) => sourceId !== String(id));
    onChangeTemplateStarters(newTemplateStarters);
  };

  const handleAddTemplateStarters = ({ id, optionType }: Pick<TUsersDropdownOption, 'id' | 'optionType'>) => {
    if (!isSubscribed && billingPlan !== ESubscriptionPlan.Free) return;
    const newStarter: ITemplateStarter = {
      sourceId: String(id),
      apiName: createStarterApiName(),
      type: optionType as unknown as ETemplateStarterType,
    };
    onChangeTemplateStarters([...templateStarters, newStarter]);
  };

  return (
    <>
      <UsersDropdown
        isMulti
        className={styles['dropdown']}
        placeholder={formatMessage({ id: 'template.starters-dropdown-placeholder' })}
        options={option}
        onChange={handleAddTemplateStarters}
        onChangeSelected={handleRemoveTemplateStarter}
        value={[...tplStarterDropdownValueUsers, ...tplStarterDropdownValueGroup]}
        onUsersInvited={({ id, optionType }) => handleAddTemplateStarters({ id, optionType })}
        onClickInvite={() => trackInviteTeamInPage('Template starters')}
        inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
      />
      <div className={styles['starters-list']}>
        {templateStarters.map(({ sourceId, type }) => {
          return (
            <UserDataWithGroup key={sourceId} idItem={Number(sourceId)} type={type as unknown as ETemplateOwnerType}>
              {(user) => {
                return (
                  <StarterItem
                    userData={user?.type !== ETemplateOwnerType.UserGroup ? user : undefined}
                    groupData={user?.type === ETemplateOwnerType.UserGroup ? user : undefined}
                    onRemove={() => handleRemoveTemplateStarter({ id: Number(sourceId) })}
                  />
                );
              }}
            </UserDataWithGroup>
          );
        })}
      </div>
    </>
  );
}