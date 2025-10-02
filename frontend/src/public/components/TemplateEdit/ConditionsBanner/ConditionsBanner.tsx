import * as React from 'react';
import { useIntl } from 'react-intl';
import { Banner } from '../../UI/Banner';

const CONDITIONS_BANNER_LS_KEY = 'conditionsBanner';

export function ConditionsBanner() {
  const { formatMessage } = useIntl();

  return (
    <Banner
      lsKey={CONDITIONS_BANNER_LS_KEY}
      text={formatMessage({ id: 'templates.conditions-banner-text' })}
      buttonText={formatMessage({ id: 'templates.conditions-banner-button' })}
      link="https://support.pneumatic.app/en/articles/5249989-conditional-workflow-logic"
    />
  );
}
