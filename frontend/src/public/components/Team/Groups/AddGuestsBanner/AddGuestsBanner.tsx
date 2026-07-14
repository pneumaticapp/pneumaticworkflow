import * as React from 'react';
import { useIntl } from 'react-intl';
import { Banner } from '../../../UI/Banner';

const ADD_GROUPS_BANNER_LS_KEY = 'addGroupsBanner';

export function AddGuestsBanner() {
  const { formatMessage } = useIntl();

  return (
    <Banner
      lsKey={ADD_GROUPS_BANNER_LS_KEY}
      text={formatMessage({ id: 'team.add-groups-banner-text' })}
      buttonText={formatMessage({ id: 'team.add-groups-banner-button' })}
      link="https://support.pneumatic.app/articles/10837733-user-groups"
    />
  );
}
