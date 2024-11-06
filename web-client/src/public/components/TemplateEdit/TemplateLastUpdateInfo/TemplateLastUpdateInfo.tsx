import * as React from 'react';

import { IntlMessages } from '../../IntlMessages';
import { UserData } from '../../UserData';
import { getUserFullName } from '../../../utils/users';
import { DateFormat } from '../../UI/DateFormat';

import styles from './TemplateLastUpdateInfo.css';

interface ITemplateLastUpdateInfoProps {
  dateUpdated: string | null;
  updatedBy: number | null;
}

export function TemplateLastUpdateInfo({ dateUpdated, updatedBy }: ITemplateLastUpdateInfoProps) {
  if (!dateUpdated && !updatedBy) {
    return null;
  }

  return (
    <div className={styles['container']}>
      <IntlMessages id="template.last-updated" />

      {updatedBy && (
        <UserData userId={updatedBy}>
          {(user) => {
            if (!user) {
              return null;
            }

            return <IntlMessages id="template.last-updated-user" values={{ user: getUserFullName(user) }} />;
          }}
        </UserData>
      )}
      {dateUpdated && (
        <IntlMessages id="template.last-updated-date" values={{ date: <DateFormat date={dateUpdated} /> }} />
      )}
    </div>
  );
}
