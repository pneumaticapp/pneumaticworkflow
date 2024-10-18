import React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { Avatar } from '../../UI/Avatar';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { UserData } from '../../UserData';
import { getNotDeletedUsers, getUserFullName } from '../../../utils/users';
import { DeleteIcon } from '../../icons';
import { ITemplate } from '../../../types/template';
import { getIsUserSubsribed, getUsers } from '../../../redux/selectors/user';
import { EOptionTypes, TUsersDropdownOption, UsersDropdown } from '../../UI/form/UsersDropdown';

import styles from './TemplateOwners.css';

interface ITemplateOwnersProps {
  templateOwners: ITemplate['templateOwners'];
  onChangeTemplateOwners(templateOwners: number[]): void;
}

export function TemplateOwners({ templateOwners = [], onChangeTemplateOwners }: ITemplateOwnersProps) {
  const { formatMessage } = useIntl();

  const users = getNotDeletedUsers(useSelector(getUsers));
  const isSubscribed = useSelector(getIsUserSubsribed);

  const mapUsersDropdownValue = users.filter((user) => templateOwners.find((id) => user.id === id));

  const templateOwnerDropdownOption = users.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.User,
      label: getUserFullName(item),
      value: String(item.id),
    };
  });
  const templateOwnerDropdownValue = mapUsersDropdownValue.map((item) => {
    return {
      ...item,
      optionType: EOptionTypes.User,
      label: getUserFullName(item),
      value: String(item.id),
    };
  });

  const handleRemoveTemplateOwner = ({ id }: Pick<TUsersDropdownOption, 'id'>) => {
    const newTemplateOwners = templateOwners.filter((userId) => userId !== id);
    onChangeTemplateOwners(newTemplateOwners);
  };

  const handleAddTemplateOwners = ({ id }: Pick<TUsersDropdownOption, 'id'>) => {
    if (!isSubscribed) return;

    onChangeTemplateOwners([...templateOwners, id]);
  };

  return (
    <>
      <UsersDropdown
        isMulti
        className={styles['dropdown']}
        placeholder={formatMessage({ id: 'user.search-field-placeholder' })}
        options={templateOwnerDropdownOption}
        onChange={handleAddTemplateOwners}
        onChangeSelected={handleRemoveTemplateOwner}
        value={templateOwnerDropdownValue}
        onUsersInvited={({ id }) => handleAddTemplateOwners({ id })}
        onClickInvite={() => trackInviteTeamInPage('Template owners')}
        inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
      />
      <div className={styles['users']}>
        {templateOwners.map((userId) => {
          return (
            <UserData userId={userId} key={`${userId}userData`}>
              {(user) => {
                if (!user) {
                  return null;
                }

                return (
                  <div key={userId} className={styles['user']}>
                    <Avatar size="lg" user={user} />
                    <div className={styles['user-info']}>
                      <span className={styles['user-name']} title={getUserFullName(user)}>
                        {getUserFullName(user)}
                      </span>
                      <span className={styles['user-role']}>
                        {user.isAdmin
                          ? formatMessage({ id: 'template.owner-admin' })
                          : formatMessage({ id: 'template.owner-starter' })}
                      </span>
                    </div>
                    <DeleteIcon
                      onClick={() => handleRemoveTemplateOwner({ id: userId })}
                      className={styles['user-delete']}
                    />
                  </div>
                );
              }}
            </UserData>
          );
        })}
      </div>
    </>
  );
}
