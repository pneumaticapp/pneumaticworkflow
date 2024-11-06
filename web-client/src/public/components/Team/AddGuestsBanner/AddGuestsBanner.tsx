import * as React from 'react';
import { useIntl } from 'react-intl';
import { Banner } from '../../UI/Banner';

const ADD_GUESTS_BANNER_LS_KEY = 'addGuestsBanner';

export function AddGuestsBanner() {
  const { formatMessage } = useIntl();

  return (
    <Banner
      lsKey={ADD_GUESTS_BANNER_LS_KEY}
      text={formatMessage({ id: 'team.add-guests-banner-text' })}
      buttonText={formatMessage({ id: 'team.add-guests-banner-button' })}
      link="https://support.pneumatic.app/en/articles/6145048-free-external-users"
    />
  );
}
