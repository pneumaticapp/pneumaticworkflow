import React from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';

import { ActivityIcon, BoxesIcon, EnableIcon, TrashIcon, UnionIcon } from '../../icons';
import { IntlMessages } from '../../IntlMessages';
import { Button } from '../../UI/Buttons/Button';
import { ShowMore } from '../../UI/ShowMore';
import { ETemplateOwnerRole } from '../../../types/template';
import { ETemplateStatus } from '../../../types/redux';
import { isCreateTemplate } from '../../../utils/history';
import { getLinkToHighlightsByTemplate } from '../../../utils/routes/getLinkToHighlightsByTemplate';
import { getLinkToWorkflows } from '../../../utils/routes/getLinkToWorkflows';
import { TemplateOwners } from '../TemplateOwners';
import { TemplateStarters } from '../TemplateStarters';
import { TemplateViewers } from '../TemplateViewers';
import {
  ITemplateControlButtonsProps,
  ITemplateMoreSettingsProps,
  ITemplateNotificationSettingsProps,
  ITemplateOwnersSettingsProps,
} from './types';

import styles from './TemplateControlls.css';

export function TemplateOwnersSettings({ owners, setFieldValue }: ITemplateOwnersSettingsProps) {
  const { formatMessage } = useIntl();
  const viewers = owners.filter(({ role }) => role === ETemplateOwnerRole.Viewer);
  const starters = owners.filter(({ role }) => role === ETemplateOwnerRole.Starter);
  const templateOwners = owners.filter(({ role }) => role === ETemplateOwnerRole.Owner);

  return (
    <>
      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.owners' })} isInitiallyVisible={isCreateTemplate()}>
          <TemplateOwners
            templateOwners={templateOwners}
            onChangeTemplateOwners={(nextOwners) =>
              setFieldValue('owners', [...nextOwners, ...viewers, ...starters], false)
            }
          />
        </ShowMore>
      </div>

      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.viewers' })}>
          <TemplateViewers
            templateViewers={viewers}
            onChangeTemplateViewers={(nextViewers) =>
              setFieldValue('owners', [...templateOwners, ...nextViewers, ...starters], false)
            }
          />
        </ShowMore>
      </div>

      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.starters' })}>
          <TemplateStarters
            templateStarters={starters}
            onChangeTemplateStarters={(nextStarters) =>
              setFieldValue('owners', [...templateOwners, ...viewers, ...nextStarters], false)
            }
          />
        </ShowMore>
      </div>
    </>
  );
}

export function TemplateMoreSettings({ templateId, onClone, onDelete }: ITemplateMoreSettingsProps) {
  const { formatMessage } = useIntl();

  return (
    <div className={styles['settings-block']}>
      <ShowMore
        label={formatMessage({ id: 'template.more' })}
        toggleClassName={classnames(!templateId && styles['more_disabled'])}
      >
        {templateId && (
          <>
            <Link
              to={getLinkToWorkflows({ templateId })}
              className={styles['more-setting']}
              onClick={() => sessionStorage.setItem('isInternalNavigation', 'true')}
            >
              <BoxesIcon className={styles['more-setting__icon']} />
              <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-show-workflows' })}</p>
            </Link>
            <Link to={getLinkToHighlightsByTemplate(templateId)} className={styles['more-setting']}>
              <ActivityIcon className={styles['more-setting__icon']} />
              <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-show-activity' })}</p>
            </Link>
            <button type="button" onClick={onClone} className={styles['more-setting']}>
              <UnionIcon className={styles['more-setting__icon']} />
              <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-clone-template' })}</p>
            </button>
            <button
              type="button"
              onClick={onDelete}
              className={classnames(styles['more-setting'], styles['more-setting_warning'])}
            >
              <TrashIcon className={styles['more-setting__icon']} />
              <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-delete-template' })}</p>
            </button>
          </>
        )}
      </ShowMore>
    </div>
  );
}

export function TemplateNotificationSettings({
  finalizable,
  completionNotification,
  reminderNotification,
  setFieldValue,
}: ITemplateNotificationSettingsProps) {
  const settings = [
    ['templates.enable-to-complete-workflow', 'finalizable', finalizable],
    ['templates.notify-on-completion', 'completionNotification', completionNotification],
    ['templates.daily-reminder', 'reminderNotification', reminderNotification],
  ] as const;

  return (
    <div className={styles['info-controls-switch']}>
      {settings.map(([label, field, checked]) => (
        <div className={styles['info-control']} key={field}>
          <div className={styles['switch-label']}>
            <IntlMessages id={label} />
          </div>
          <Switch
            className={classnames(
              'custom-switch custom-switch-primary custom-switch-small ml-auto',
              styles['info-control_switch'],
            )}
            checked={checked}
            checkedChildren={null}
            unCheckedChildren={null}
            onChange={(value) => setFieldValue(field, value, false)}
          />
        </div>
      ))}
    </div>
  );
}

export function TemplateControlButtons({
  isActive,
  isActivating,
  templateStatus,
  onToggleActive,
  onRun,
}: ITemplateControlButtonsProps) {
  const { formatMessage } = useIntl();
  const showEnableButton = !isActive || isActivating;

  return (
    <div className={styles['control-buttons']}>
      <div className={styles['control-buttons_adjacents']}>
        <Button
          size="md"
          className={classnames(
            styles['control-button'],
            styles['enable-button'],
            showEnableButton ? styles['enable-button_enable'] : styles['enable-button_disable'],
          )}
          type="button"
          onClick={onToggleActive}
          label={showEnableButton ? formatMessage({ id: 'templates.enable-template-button' }) : ''}
          buttonStyle="yellow"
          icon={EnableIcon}
          isLoading={isActivating}
        />
        <Button
          size="md"
          className={classnames(
            styles['control-button'],
            styles['run-button'],
            showEnableButton && styles['run-button_non-active'],
          )}
          type="button"
          onClick={onRun}
          disabled={templateStatus !== ETemplateStatus.Saved || !isActive}
          label={formatMessage({ id: 'templates.run-workflow' })}
          buttonStyle="transparent-black"
        />
      </div>
    </div>
  );
}
