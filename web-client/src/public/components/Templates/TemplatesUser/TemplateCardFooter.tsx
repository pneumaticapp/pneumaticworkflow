import React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { IntlMessages } from '../../IntlMessages';
import { getPluralNoun } from '../../../utils/helpers';
import { PlayLogoIcon, WarningIcon } from '../../icons';
import { Button, Tooltip } from '../../UI';
import { EIntegrations } from '../../../types/integrations';
import { TemplateIntegrationsIndicator, useTemplateIntegrationsList } from '../../TemplateIntegrationsStats';

import { checkShowDraftTemplateWarning } from '../utils/checkShowDraftTemplateWarning';

import styles from '../Templates.css';

export interface ITemplateCardFooterProps {
  templateId: number;
  tasksCount: number;
  isActive: boolean;
  isPublic: boolean;
  onRunWorkflow(): void;
}

export function TemplateCardFooter({
  templateId,
  tasksCount,
  isActive,
  isPublic,
  onRunWorkflow,
}: ITemplateCardFooterProps) {
  const { formatMessage } = useIntl();
  const templateIntegrations = useTemplateIntegrationsList(templateId);
  const showDraftWarning = checkShowDraftTemplateWarning(isActive, isPublic, templateIntegrations);

  const renderRunWorkflowButton = () => {
    return (
      <Button
        icon={PlayLogoIcon}
        size='md'
        onClick={onRunWorkflow}
        buttonStyle="yellow"
        aria-label={formatMessage({ id: 'templates.run-workflow-hint' })}
      />
    );
  }

  const renderDraftLabel = () => {
    if (isActive) {
      return null;
    }

    if (showDraftWarning) {
      return (
        <Tooltip content={formatMessage({ id: 'templates.draft-warning' })}>
          <div className={styles['card-draft']}>
            <div className={styles['card-draft__warning-icon']}>
              <WarningIcon />
            </div>
          </div>
        </Tooltip>
      );
    }

    return (
      <div className={styles['card-draft']}>
        <IntlMessages id="template.card-draft" />
      </div>
    );
  };

  const renderCardStats = () => {
    if (!tasksCount) {
      return null;
    }

    return (
      <div className={styles['card-stats']}>
        <div>
          <span className={styles['card-stats__amount']}>
            {tasksCount}
          </span>
          &nbsp;
          <span>
            {getPluralNoun({
              counter: tasksCount,
              single: 'step',
              plural: 'steps',
            })}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={styles['card__footer']}>
      <div className={styles['card-footer__left']}>
        <TemplateIntegrationsIndicator
          templateId={templateId}
          exlcude={[EIntegrations.Webhooks]}
          integratedIndicator={(
            <div className={classnames(styles['card-integration'], styles['card-integration_integrated'])}>
              {formatMessage({ id: 'templates.template-integrated' })}
            </div>
          )}
          disconnectedIndicator={(
            <div className={classnames(styles['card-integration'], styles['card-integration_not-integrated'])}>
              {formatMessage({ id: 'templates.template-not-integrated' })}
            </div>
          )}
        />

        {renderCardStats()}
      </div>
      <div className={styles['card-footer__right']}>
        {isActive ? renderRunWorkflowButton() : renderDraftLabel()}
      </div>
    </div>
  );
}
