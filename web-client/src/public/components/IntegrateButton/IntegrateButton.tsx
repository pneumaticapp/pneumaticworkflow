import * as React from 'react';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';
import OutsideClickHandler from 'react-outside-click-handler';

import { IntegrateIcon } from '../icons';
import { Tooltip, Button } from '../UI';
import { TemplateIntegrationsStats, getIntegrationsSettings } from '../TemplateIntegrationsStats';
import { EIntegrations } from '../../types/integrations';
import { useCheckDevice } from '../../hooks/useCheckDevice';

import styles from './IntegrateButton.css';

type TIntegrateButtonConditionalProps = {
  linksType: 'relative';
  tepmlateId: number;
} | {
  linksType: 'anchors';
  tepmlateId?: never;
}

export type TIntegrateButtonCommonProps = {
  isVisible: boolean;
  tepmlateId?: number;
  buttonSize?: React.ComponentProps<typeof Button>['size'];
  buttonClassname?: string;
  toggle(): void;
}

type TIntegrateButtonProps = TIntegrateButtonCommonProps & TIntegrateButtonConditionalProps;

export function IntegrateButton({
  isVisible,
  tepmlateId,
  buttonSize = 'sm',
  buttonClassname,
  linksType,
  toggle,
}: TIntegrateButtonProps) {
  const { isDesktop } = useCheckDevice();
  const integrationsSettings = getIntegrationsSettings(tepmlateId);

  const { formatMessage } = useIntl();

  return (
    <Tooltip
      isDarkBackground
      visible={isVisible}
      size="lg"
      content={(
        <OutsideClickHandler
          disabled={!isVisible}
          onOutsideClick={toggle}
        >
          <div className={styles.integrations}>
            {Object.entries(integrationsSettings)
              .map(([integration, { title, description, link, anchor }]) => (
                // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions
                <div className={styles.integration} onClick={event => event.stopPropagation()}>
                  <div className={styles.integration__header}>
                    <Link
                      to={linksType === 'anchors' ? anchor : link as string}
                      onClick={toggle}
                      className={styles.integration__title}
                    >
                      {title}
                    </Link>
                    <TemplateIntegrationsStats templateId={tepmlateId}>
                      {(connectedIntegrations) => (connectedIntegrations.includes(integration as EIntegrations) && (
                        <p className={styles['integration__is_used']}>
                          {formatMessage({ id: 'dashboard.integration-used' })}
                        </p>
                      ))}
                    </TemplateIntegrationsStats>
                  </div>
                  <p className={styles['integration__description']}>
                    {description}
                  </p>
                </div>
              ))}
          </div>
        </OutsideClickHandler>
      )}
      placement={isDesktop ? 'right' : 'bottom'}
      trigger="click"
    >
      <Button
        size={buttonSize}
        className={buttonClassname}
        buttonStyle="black"
        label="Integrate"
        wrapper="button"
        type="button"
        icon={IntegrateIcon}
        onClick={event => {
          event.stopPropagation();
          toggle();
        }}
      />
    </Tooltip >
  )
}
