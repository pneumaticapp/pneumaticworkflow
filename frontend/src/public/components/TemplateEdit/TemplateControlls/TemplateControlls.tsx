import * as React from 'react';
import { useEffect, useState } from 'react';
import Switch from 'rc-switch';
import { Link } from 'react-router-dom';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { useSelector } from 'react-redux';
import { TemplateOwners } from '../TemplateOwners';
import { TemplateViewers } from '../TemplateViewers';
import { TemplateStarters } from '../TemplateStarters';
import { ActivityIcon, BoxesIcon, EnableIcon, TrashIcon, UnionIcon, WarningIcon } from '../../icons';
import { IntlMessages } from '../../IntlMessages';
import { ShowMore } from '../../UI/ShowMore';
import { getLinkToWorkflows } from '../../../utils/routes/getLinkToWorkflows';
import { getLinkToHighlightsByTemplate } from '../../../utils/routes/getLinkToHighlightsByTemplate';
import { Button } from '../../UI/Buttons/Button';
import { ETemplateOwnerRole, ITemplateOwner, ITemplateClient } from '../../../types/template';
import { TCloneTemplatePayload, TDeleteTemplatePayload, TPatchTemplatePayload } from '../../../redux/actions';
import { getRunnableWorkflow, loadDatasetsMap } from '../utils/getRunnableWorkflow';
import { mapFieldsetBindingClientToRuntime } from '../../../utils/mapFieldsetBindingClientToRuntime';
import { ETemplateStatus } from '../../../types/redux';
import { IRunWorkflow } from '../../WorkflowEditPopup/types';
import { WarningPopup } from '../../UI/WarningPopup';
import { isCreateTemplate } from '../../../utils/history';
import { InfoWarningsModal } from '../InfoWarningsModal';
import { useTemplateActivation } from '../../../hooks/useTemplateActivation';
import { useTemplateIntegrationsList } from '../../TemplateIntegrationsStats';
import { checkShowDraftTemplateWarning } from '../../Templates';

import styles from './TemplateControlls.css';
import { getSubscriptionPlan } from '../../../redux/selectors/user';
import { ESubscriptionPlan } from '../../../types/account';

export interface ITemplateControllsProps {
  template: ITemplateClient;
  templateStatus: ETemplateStatus;
  isSubscribed: boolean;
  cloneTemplate(payload: TCloneTemplatePayload): void;
  patchTemplate(payload: TPatchTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
  openRunWorkflowModal(payload: IRunWorkflow): void;
  onTemplateDeleted(): void;
}

export function TemplateControlls({
  template,
  templateStatus,
  isSubscribed,
  patchTemplate,
  cloneTemplate,
  deleteTemplate,
  openRunWorkflowModal,
  onTemplateDeleted,
}: ITemplateControllsProps) {
  const { formatMessage } = useIntl();
  const billingPlan = useSelector(getSubscriptionPlan);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;
  const { isActivating, infoWarnings, isInfoWarningsOpen, closeInfoWarnings, setTemplateActive } =
    useTemplateActivation({ template, accessConditions, patchTemplate });

  const templateIntegrations = useTemplateIntegrationsList(template.id);
  const [showDraftWarning, setShowDraftWarning] = useState(
    checkShowDraftTemplateWarning(template.isActive, template.isPublic, templateIntegrations),
  );
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  useEffect(() => {
    // sets warning only when integrations are initially loaded
    setShowDraftWarning(checkShowDraftTemplateWarning(template.isActive, template.isPublic, templateIntegrations));
  }, [JSON.stringify(templateIntegrations)]);

  useEffect(() => {
    if (template.isActive) {
      setShowDraftWarning(false);
    }
  }, [template.isActive]);

  const {
    id: templateId,
    name: templateName,
    owners,
    isActive: isTemplateActive,
    finalizable: isTemplateFinalizable,
    completionNotification: isCompletionNotification,
    reminderNotification: isReminderNotification,
  } = template;

  const viewers = owners.filter((o: ITemplateOwner) => o.role === ETemplateOwnerRole.Viewer);
  const starters = owners.filter((o: ITemplateOwner) => o.role === ETemplateOwnerRole.Starter);
  const pureOwners = owners.filter((o: ITemplateOwner) => o.role === ETemplateOwnerRole.Owner);

  const isSavedTemplate = React.useMemo(() => Boolean(templateId), [templateId]);

  const handleRunProcess = async () => {
    if (!template.id) return;
    const loadedFieldsets = template.kickoff.fieldsets.map(mapFieldsetBindingClientToRuntime);
    const datasetsMap = await loadDatasetsMap(template.kickoff, loadedFieldsets);
    const runnableWorkflow = getRunnableWorkflow(template, datasetsMap, loadedFieldsets);
    if (runnableWorkflow) {
      openRunWorkflowModal(runnableWorkflow);
    }
  };

  const renderDeleteTemplateModal = () => {
    if (!templateId) {
      return null;
    }

    const onDeleteTemplate = () => {
      onTemplateDeleted();
      deleteTemplate({ templateId });
    };

    return (
      <WarningPopup
        acceptTitle={formatMessage({ id: 'template.remove-accept' })}
        declineTitle={formatMessage({ id: 'template.remove-cancel' })}
        title={formatMessage({ id: 'template.remove-title' })}
        message={formatMessage({ id: 'template.remove-message' }, { template: <strong>{templateName}</strong> })}
        closeModal={() => setIsDeleteModalOpen(false)}
        isOpen={isDeleteModalOpen}
        onConfirm={onDeleteTemplate}
        onReject={() => setIsDeleteModalOpen(false)}
      />
    );
  };

  const renderControllButtons = () => {
    const showEnableTemplateButton = !isTemplateActive || isActivating;

    return (
      <div className={styles['control-buttons']}>
        <div className={styles['control-buttons_adjacents']}>
          <Button
            size="md"
            className={classnames(
              styles['control-button'],
              styles['enable-button'],
              showEnableTemplateButton ? styles['enable-button_enable'] : styles['enable-button_disable'],
            )}
            type="button"
            onClick={() => setTemplateActive(!isTemplateActive)}
            label={showEnableTemplateButton ? formatMessage({ id: 'templates.enable-template-button' }) : ''}
            buttonStyle="yellow"
            icon={EnableIcon}
            isLoading={isActivating}
          />
          <Button
            size="md"
            className={classnames(
              styles['control-button'],
              styles['run-button'],
              showEnableTemplateButton && styles['run-button_non-active'],
            )}
            type="button"
            onClick={handleRunProcess}
            disabled={templateStatus !== ETemplateStatus.Saved || !isTemplateActive}
            label={formatMessage({ id: 'templates.run-workflow' })}
            buttonStyle="transparent-black"
          />
        </div>
      </div>
    );
  };

  return (
    <>
      {renderDeleteTemplateModal()}
      <InfoWarningsModal isOpen={isInfoWarningsOpen} onClose={closeInfoWarnings} warnings={infoWarnings} />

      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.owners' })} isInitiallyVisible={isCreateTemplate()}>
          <TemplateOwners
            templateOwners={pureOwners}
            onChangeTemplateOwners={(newTemplateOwners) =>
              patchTemplate({ changedFields: { owners: [...newTemplateOwners, ...viewers, ...starters] } })
            }
          />
        </ShowMore>
      </div>

      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.viewers' })}>
          <TemplateViewers
            templateViewers={viewers}
            onChangeTemplateViewers={(newViewers) =>
              patchTemplate({ changedFields: { owners: [...pureOwners, ...newViewers, ...starters] } })
            }
          />
        </ShowMore>
      </div>

      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.starters' })}>
          <TemplateStarters
            templateStarters={starters}
            onChangeTemplateStarters={(newStarters) =>
              patchTemplate({ changedFields: { owners: [...pureOwners, ...viewers, ...newStarters] } })
            }
          />
        </ShowMore>
      </div>

      <div className={styles['settings-block']}>
        <ShowMore
          label={formatMessage({ id: 'template.more' })}
          toggleClassName={classnames(!isSavedTemplate && styles['more_disabled'])}
        >
          {templateId && (
            <>
              <Link
                to={getLinkToWorkflows({
                  templateId,
                })}
                className={styles['more-setting']}
                onClick={() => {
                  sessionStorage.setItem('isInternalNavigation', 'true');
                }}
              >
                <BoxesIcon className={styles['more-setting__icon']} />
                <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-show-workflows' })}</p>
              </Link>
              <Link to={getLinkToHighlightsByTemplate(templateId)} className={styles['more-setting']}>
                <ActivityIcon className={styles['more-setting__icon']} />
                <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-show-activity' })}</p>
              </Link>

              <button type="button" onClick={() => cloneTemplate({ templateId })} className={styles['more-setting']}>
                <UnionIcon className={styles['more-setting__icon']} />
                <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-clone-template' })}</p>
              </button>
              <button
                type="button"
                onClick={() => setIsDeleteModalOpen(true)}
                className={classnames(styles['more-setting'], styles['more-setting_warning'])}
              >
                <TrashIcon className={styles['more-setting__icon']} />
                <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-delete-template' })}</p>
              </button>
            </>
          )}
        </ShowMore>
      </div>

      <div className={styles['info-controls-switch']}>
        <div className={styles['info-control']}>
          <div className={styles['switch-label']}>
            <IntlMessages id="templates.enable-to-complete-workflow" />
          </div>
          <Switch
            className={classnames(
              'custom-switch custom-switch-primary custom-switch-small ml-auto',
              styles['info-control_switch'],
            )}
            checked={isTemplateFinalizable}
            checkedChildren={null}
            unCheckedChildren={null}
            onChange={(value) => patchTemplate({ changedFields: { finalizable: value } })}
          />
        </div>
        <div className={styles['info-control']}>
          <div className={styles['switch-label']}>
            <IntlMessages id="templates.notify-on-completion" />
          </div>
          <Switch
            className={classnames(
              'custom-switch custom-switch-primary custom-switch-small ml-auto',
              styles['info-control_switch'],
            )}
            checked={isCompletionNotification}
            checkedChildren={null}
            unCheckedChildren={null}
            onChange={(value) => patchTemplate({ changedFields: { completionNotification: value } })}
          />
        </div>
        <div className={styles['info-control']}>
          <div className={styles['switch-label']}>
            <IntlMessages id="templates.daily-reminder" />
          </div>
          <Switch
            className={classnames(
              'custom-switch custom-switch-primary custom-switch-small ml-auto',
              styles['info-control_switch'],
            )}
            checked={isReminderNotification}
            checkedChildren={null}
            unCheckedChildren={null}
            onChange={(value) => patchTemplate({ changedFields: { reminderNotification: value } })}
          />
        </div>
      </div>

      {showDraftWarning && (
        <div className={styles['external-links-warning']}>
          <div className={styles['external-links-warning__icon']}>
            <WarningIcon />
          </div>
          <p className={styles['external-links-warning__text']}>{formatMessage({ id: 'templates.draft-warning' })}</p>
        </div>
      )}

      {renderControllButtons()}
    </>
  );
}
