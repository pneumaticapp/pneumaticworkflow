import React from 'react';
import { useIntl } from 'react-intl';
import { Banner } from '../../UI/Banner';
import { ELearnMoreLinks } from '../../../constants/defaultValues';

const GUEST_BANNER_LS_KEY = 'tenantGuestBanner';

export function TenantGuestBanner() {
  const { formatMessage } = useIntl();

  return (
    <Banner
      lsKey={GUEST_BANNER_LS_KEY}
      text={formatMessage({ id: 'tenants.promo-title' })}
      buttonText={formatMessage({ id: 'tenants.promo-button' })}
      link={ELearnMoreLinks.TenantsModal}
    />
  );
}
