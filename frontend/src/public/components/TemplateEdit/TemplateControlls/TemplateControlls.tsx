import React, { useEffect, useState } from 'react';
import Switch from 'rc-switch';
import { Link } from 'react-router-dom';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { TemplateOwners } from '../TemplateOwners';
import { TemplateViewers } from '../TemplateViewers';
import { TemplateStarters } from '../TemplateStarters';
import { ActivityIcon, BoxesIcon, EnableIcon, TrashIcon, UnionIcon, WarningIcon } from '../../icons';
import { IntlMessages } from '../../IntlMessages';
import { ShowMore } from '../../UI/ShowMore';
import { getLinkToWorkflows } from '../../../utils/routes/getLinkToWorkflows';
import { getLinkToHighlightsByTemplate } from '../../../utils/routes/getLinkToHighlightsByTemplate';
import { Button } from '../../UI/Buttons/Button';
import { ETemplateOwnerRole, ITemplateOwner, ITemplate } from '../../../types/template';
import {
  TCloneTemplatePayload,
  TDeleteTemplatePayload,
  TPatchTemplatePayload,
  discardTemplateChanges,
} from '../../../redux/actions';
import { getRunnableWorkflow, loadDatasetsMap } from '../utils/getRunnableWorkflow';
import { ETemplateStatus } from '../../../types/redux';
import { getTemplateStatus } from '../../../redux/selectors/template';
import { IRunWorkflow } from '../../WorkflowEditPopup/types';
import { WarningPopup } from '../../UI/WarningPopup';
import { validateTemplate } from '../utils/validateTemplate';
import { isArrayWithItems } from '../../../utils/helpers';
import { NotificationManager } from '../../UI/Notifications';
import { IInfoWarningProps } from '../InfoWarningsModal';
import { isCreateTemplate, history, checkSomeRouteMatchesLocation } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import { RouteLeavingGuard } from '../../UI';
import { useTemplateIntegrationsList } from '../../TemplateIntegrationsStats';
import { checkShowDraftTemplateWarning } from '../../Templates';

import styles from './TemplateControlls.css';
import { getSubscriptionPlan, getIsUserSubsribed } from '../../../redux/selectors/user';
import { ESubscriptionPlan } from '../../../types/account';
import { useTemplateField, useTemplatePersist } from '../useTemplateForm';

export interface ITemplateControllsProps {
  cloneTemplate(payload: TCloneTemplatePayload): void;
  patchTemplate(payload: TPatchTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
  openRunWorkflowModal(payload: IRunWorkflow): void;
  setInfoWarnings(infoWarnings: ((props: IInfoWarningProps) => JSX.Element)[]): void;
}

export function TemplateControlls({
  patchTemplate,
  cloneTemplate,
  deleteTemplate,
  openRunWorkflowModal,
  setInfoWarnings,
}: ITemplateControllsProps) {
  const intl = useIntl();
  const { formatMessage } = intl;
  const dispatch = useDispatch();
  const { values: template, setFieldValue, setValues } = useTemplateField();
  const {
    consumePendingChanges,
    confirmConsumedChanges,
    revertConsumedChanges,
    abandonPendingChanges,
  } = useTemplatePersist();
  const templateStatus = useSelector(getTemplateStatus);
  const isSubscribed = useSelector(getIsUserSubsribed);
  const billingPlan = useSelector(getSubscriptionPlan);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;

  const templateIntegrations = useTemplateIntegrationsList(template.id);
  const [showDraftWarning, setShowDraftWarning] = useState(
    checkShowDraftTemplateWarning(template.isActive, template.isPublic, templateIntegrations),
  );
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isTemplateActivating, setIsTemplateActivating] = useState(false);
  const [isTemplateDeleted, setIsTemplateDeleted] = useState(false);

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
    const datasetsMap = await loadDatasetsMap(template.kickoff);
    const runnableWorkflow = getRunnableWorkflow(template, datasetsMap);
    if (runnableWorkflow) {
      openRunWorkflowModal(runnableWorkflow);
    }
  };

  const handleChangeIsActive = (value: ITemplate['isActive'], redirectUrl?: string) => {
    if (!value) {
      const valuesSnapshot = template;
      const pendingChanges = consumePendingChanges({ isActive: false });

      patchTemplate({
        changedFields: { ...pendingChanges, isActive: false },
        onSuccess: confirmConsumedChanges,
        onFailed: () => {
          setValues(valuesSnapshot);
          revertConsumedChanges();
        },
      });
      return;
    }

    const { commonWarnings, infoWarnings } = validateTemplate(template, accessConditions, intl);
    if (isArrayWithItems(infoWarnings)) {
      setInfoWarnings(infoWarnings);
      return;
    }
    if (isArrayWithItems(commonWarnings)) {
      commonWarnings.forEach((message) => NotificationManager.warning({ message }));
      return;
    }

    setIsTemplateActivating(true);

    const valuesSnapshot = template;
    const pendingChanges = consumePendingChanges({ isActive: true });

    patchTemplate({
      changedFields: {
        ...pendingChanges,
        isActive: true,
      },
      onSuccess: () => {
        confirmConsumedChanges();
        setIsTemplateActivating(false);

        if (redirectUrl) {
          history.push(redirectUrl);
        }
      },
      onFailed: () => {
        setValues(valuesSnapshot);
        revertConsumedChanges();
        setIsTemplateActivating(false);
      },
    });
  };

  const renderDeleteTemplateModal = () => {
    if (!templateId) {
      return null;
    }

    const onDeleteTemplate = () => {
      setIsTemplateDeleted(true);
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

  const renderLeavingGuard = () => {
    const showLeavingGuard = !template.isActive && !isTemplateDeleted;

    return (
      <RouteLeavingGuard
        when={showLeavingGuard}
        title={formatMessage({ id: 'templates.inactive-warning-title' })}
        message={formatMessage({ id: 'templates.inactive-warning-message' })}
        onConfirm={(path) => {
          handleChangeIsActive(true, path);
        }}
        onReject={(path) => {
          history.push(path);
        }}
        shouldBlockNavigation={(location) => {
          return !checkSomeRouteMatchesLocation(location.pathname, [
            ERoutes.TemplateView,
            ERoutes.TemplatesEdit,
            ERoutes.TemplatesCreate,
            ERoutes.Login,
          ]);
        }}
        renderControlls={(confirm, reject) => {
          return (
            <>
              <Button
                label={formatMessage({ id: 'templates.save-and-enable-button' })}
                onClick={confirm}
                buttonStyle="yellow"
                size="md"
              />

              <Button
                label={formatMessage({ id: 'templates.save-as-draft' })}
                onClick={reject}
                buttonStyle="transparent-black"
                size="md"
              />

              {templateId && (
                <button
                  type="button"
                  className={classnames('cancel-button', styles['keep-draf-button'])}
                  onClick={() => {
                    abandonPendingChanges();
                    dispatch(discardTemplateChanges({
                      templateId,
                      onSuccess: () => {
                        reject();
                      },
                    }));
                  }}
                >
                  {formatMessage({ id: 'templates.discard-changes' })}
                </button>
              )}
            </>
          );
        }}
      />
    );
  };

  const renderControllButtons = () => {
    const showEnableTemplateButton = !isTemplateActive || isTemplateActivating;

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
            onClick={() => handleChangeIsActive(!isTemplateActive)}
            label={showEnableTemplateButton ? formatMessage({ id: 'templates.enable-template-button' }) : ''}
            buttonStyle="yellow"
            icon={EnableIcon}
            isLoading={isTemplateActivating}
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
      {templateId && renderLeavingGuard()}

      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.owners' })} isInitiallyVisible={isCreateTemplate()}>
          <TemplateOwners
            templateOwners={pureOwners}
            onChangeTemplateOwners={(newTemplateOwners) =>
              setFieldValue('owners', [...newTemplateOwners, ...viewers, ...starters], false)
            }
          />
        </ShowMore>
      </div>

      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.viewers' })}>
          <TemplateViewers
            templateViewers={viewers}
            onChangeTemplateViewers={(newViewers) =>
              setFieldValue('owners', [...pureOwners, ...newViewers, ...starters], false)
            }
          />
        </ShowMore>
      </div>

      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.starters' })}>
          <TemplateStarters
            templateStarters={starters}
            onChangeTemplateStarters={(newStarters) =>
              setFieldValue('owners', [...pureOwners, ...viewers, ...newStarters], false)
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
            onChange={(value) => setFieldValue('finalizable', value, false)}
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
            onChange={(value) => setFieldValue('completionNotification', value, false)}
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
            onChange={(value) => setFieldValue('reminderNotification', value, false)}
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
