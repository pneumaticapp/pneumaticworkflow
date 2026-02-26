import React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { IApplicationState } from '../../../types/redux';
import { ESubscriptionPlan } from '../../../types/account';
import { createViewerApiName } from '../../../utils/createId';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { getNotDeletedUsers, getUserFullName } from '../../../utils/users';
import { EOptionTypes, TUsersDropdownOption, UsersDropdown } from '../../UI/form/UsersDropdown';
import { getIsUserSubsribed, getSubscriptionPlan, getUsers } from '../../../redux/selectors/user';
import { ETaskPerformerType, ETemplateOwnerType, ETemplateViewerType, ITemplate, ITemplateViewer } from '../../../types/template';
import ViewerItem from './components';

import styles from './TemplateViewers.css';
import UserDataWithGroup from '../../UserDataWithGroup';

interface ITemplateViewersProps {
  templateViewers: ITemplate['viewers'];
  onChangeTemplateViewers(templateViewers: ITemplateViewer[]): void;
}

export function TemplateViewers({ templateViewers = [], onChangeTemplateViewers }: ITemplateViewersProps) {
  const { formatMessage } = useIntl();

  const isSubscribed = useSelector(getIsUserSubsribed);
  const billingPlan = useSelector(getSubscriptionPlan);
  const groups = useSelector((state: IApplicationState) => state.groups.list);

  const users = getNotDeletedUsers(useSelector(getUsers));
  const mapUsersDropdownValue = users.filter((user) =>
    templateViewers.find(({ sourceId }) => Number(sourceId) === user.id),
  );

  const mapGroupDropdownValue = groups.filter((group) =>
    templateViewers.find(({ sourceId }) => Number(sourceId) === group.id),
  );

  const templateViewerGroupDropdownOption = groups.map((group) => {
    return {
      ...group,
      optionType: EOptionTypes.Group,
      type: ETaskPerformerType.UserGroup,
      label: group.name,
      value: String(group.id),
    };
  });

  const templateViewerDropdownOption = users.map((item) => {
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
    ...templateViewerGroupDropdownOption,
    ...templateViewerDropdownOption,
  ] as unknown as TUsersDropdownOption[];

  const tplViewerDropdownValueUsers = mapUsersDropdownValue.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.User,
      label: getUserFullName(item),
      value: String(item.id),
    };
  });

  const tplViewerDropdownValueGroup = mapGroupDropdownValue.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.Group,
      label: item.name,
      value: String(item.id),
    };
  });

  const handleRemoveTemplateViewer = ({ id }: Pick<TUsersDropdownOption, 'id'>) => {
    const newTemplateViewers = templateViewers.filter(({ sourceId }) => sourceId !== String(id));
    onChangeTemplateViewers(newTemplateViewers);
  };

  const handleAddTemplateViewers = ({ id, optionType }: Pick<TUsersDropdownOption, 'id' | 'optionType'>) => {
    if (!isSubscribed && billingPlan !== ESubscriptionPlan.Free) return;
    const newViewer: ITemplateViewer = {
      sourceId: String(id),
      apiName: createViewerApiName(),
      type: optionType as unknown as ETemplateViewerType,
    };
    onChangeTemplateViewers([...templateViewers, newViewer]);
  };

  return (
    <>
      <UsersDropdown
        isMulti
        className={styles['dropdown']}
        placeholder={formatMessage({ id: 'template.viewers-dropdown-placeholder' })}
        options={option}
        onChange={handleAddTemplateViewers}
        onChangeSelected={handleRemoveTemplateViewer}
        value={[...tplViewerDropdownValueUsers, ...tplViewerDropdownValueGroup]}
        onUsersInvited={({ id, optionType }) => handleAddTemplateViewers({ id, optionType })}
        onClickInvite={() => trackInviteTeamInPage('Template viewers')}
        inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
      />
      <div className={styles['viewers-list']}>
        {templateViewers.map(({ sourceId, type }) => {
          return (
            <UserDataWithGroup key={sourceId} idItem={Number(sourceId)} type={type as unknown as ETemplateOwnerType}>
              {(user) => {
                return (
                  <ViewerItem
                    userData={user?.type !== ETemplateOwnerType.UserGroup ? user : undefined}
                    groupData={user?.type === ETemplateOwnerType.UserGroup ? user : undefined}
                    onRemove={() => handleRemoveTemplateViewer({ id: Number(sourceId) })}
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