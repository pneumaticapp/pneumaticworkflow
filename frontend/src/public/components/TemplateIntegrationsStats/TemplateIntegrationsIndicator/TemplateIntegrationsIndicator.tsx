import * as React from 'react';
import { useIntl } from 'react-intl';

import { getIntegrationsSettings, TemplateIntegrationsStats } from '..';
import { ELearnMoreLinks } from '../../../constants/defaultValues';
import { isArrayWithItems } from '../../../utils/helpers';
import { Tooltip } from '../../UI';
import { ITemplateIntegrationsStatsProps } from '../TemplateIntegrationsStats';

import styles from './TemplateIntegrationsIndicator.css';

interface TemplateIntegrationsIndicatorProps extends Pick<ITemplateIntegrationsStatsProps, 'templateId' | 'exlcude'> {
  integratedIndicator: JSX.Element;
  disconnectedIndicator: JSX.Element;
}

export function TemplateIntegrationsIndicator({
  integratedIndicator,
  disconnectedIndicator,
  templateId,
  exlcude,
}: TemplateIntegrationsIndicatorProps) {
  const { formatMessage } = useIntl();
  const integrationsSettings = getIntegrationsSettings(templateId);

  return (
    <TemplateIntegrationsStats templateId={templateId} exlcude={exlcude}>
      {connectedIntegrations => {
        const indicator = isArrayWithItems(connectedIntegrations)
          ? (
            <Tooltip
              content={(
                <div className={styles['indicator-tooltip']}>
                  {connectedIntegrations.map(i => integrationsSettings[i].title).join('\n')}
                </div>
              )}
            >
             {integratedIndicator}
            </Tooltip>
          )
          : (
            <Tooltip
              content={(
                <div className={styles['indicator-tooltip']}>
                  {formatMessage({ id: 'dashboard.integrations-tooltip' })}
                  <div className={styles['indicator-tooltip__link']}>
                    <a target="_blank" href={ELearnMoreLinks.Integrations} rel="noreferrer">
                      {formatMessage({ id: 'dashboard.integrations-tooltip-link' })}
                    </a>
                  </div>
                </div>
              )}
            >
              {disconnectedIndicator}
            </Tooltip>
          );

        return indicator;
      }}
    </TemplateIntegrationsStats>
  )
}
