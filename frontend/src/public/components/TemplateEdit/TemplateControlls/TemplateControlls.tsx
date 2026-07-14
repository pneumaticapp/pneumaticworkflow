import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { WarningIcon } from '../../icons';
import { ITemplate } from '../../../types/template';
import {
  cloneTemplate,
  deleteTemplate,
  discardTemplateChanges,
  openRunWorkflowModal,
  patchTemplate,
} from '../../../redux/actions';
import { getRunnableWorkflow, loadDatasetsMap } from '../utils/getRunnableWorkflow';
import { getTemplateStatus } from '../../../redux/selectors/template';
import { validateTemplate } from '../utils/validateTemplate';
import { isArrayWithItems } from '../../../utils/helpers';
import { NotificationManager } from '../../UI/Notifications';
import { history } from '../../../utils/history';
import { useTemplateIntegrationsList } from '../../TemplateIntegrationsStats';
import { checkShowDraftTemplateWarning } from '../../Templates';

import styles from './TemplateControlls.css';
import { getSubscriptionPlan, getIsUserSubsribed } from '../../../redux/selectors/user';
import { ESubscriptionPlan } from '../../../types/account';
import { useTemplateField, useTemplatePersist } from '../useTemplateForm';
import { ITemplateControllsProps } from './types';
import {
  TemplateControlButtons,
  TemplateMoreSettings,
  TemplateNotificationSettings,
  TemplateOwnersSettings,
} from './TemplateControlsSections';
import { TemplateNavigation } from './TemplateNavigation';

export function TemplateControlls({ setInfoWarnings }: ITemplateControllsProps) {
  const intl = useIntl();
  const { formatMessage } = intl;
  const dispatch = useDispatch();
  const { values: template, setFieldValue } = useTemplateField();
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

  const handleRunProcess = async () => {
    const datasetsMap = await loadDatasetsMap(template.kickoff);
    const runnableWorkflow = getRunnableWorkflow(template, datasetsMap);
    if (runnableWorkflow) {
      dispatch(openRunWorkflowModal(runnableWorkflow));
    }
  };

  const handleChangeIsActive = (value: ITemplate['isActive'], redirectUrl?: string) => {
    if (!value) {
      const pendingChanges = consumePendingChanges({ isActive: false });

      dispatch(patchTemplate({
        changedFields: { ...pendingChanges, isActive: false },
        onSuccess: confirmConsumedChanges,
        onFailed: revertConsumedChanges,
      }));
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

    const pendingChanges = consumePendingChanges({ isActive: true });

    dispatch(patchTemplate({
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
        revertConsumedChanges();
        setIsTemplateActivating(false);
      },
    }));
  };

  return (
    <>
      <TemplateNavigation
        templateId={templateId}
        templateName={templateName}
        isActive={template.isActive}
        isDeleted={isTemplateDeleted}
        isDeleteModalOpen={isDeleteModalOpen}
        onCloseDeleteModal={() => setIsDeleteModalOpen(false)}
        onDelete={() => {
          if (templateId) {
            setIsTemplateDeleted(true);
            dispatch(deleteTemplate({ templateId }));
          }
        }}
        onActivate={(path) => handleChangeIsActive(true, path)}
        onDiscard={(onSuccess) => {
          if (templateId) {
            dispatch(discardTemplateChanges({
              templateId,
              onSuccess: () => {
                abandonPendingChanges();
                onSuccess();
              },
            }));
          }
        }}
      />

      <TemplateOwnersSettings owners={owners} setFieldValue={setFieldValue} />
      <TemplateMoreSettings
        templateId={templateId}
        onClone={() => templateId && dispatch(cloneTemplate({ templateId }))}
        onDelete={() => setIsDeleteModalOpen(true)}
      />
      <TemplateNotificationSettings
        finalizable={isTemplateFinalizable}
        completionNotification={isCompletionNotification}
        reminderNotification={isReminderNotification}
        setFieldValue={setFieldValue}
      />

      {showDraftWarning && (
        <div className={styles['external-links-warning']}>
          <div className={styles['external-links-warning__icon']}>
            <WarningIcon />
          </div>
          <p className={styles['external-links-warning__text']}>{formatMessage({ id: 'templates.draft-warning' })}</p>
        </div>
      )}

      <TemplateControlButtons
        isActive={isTemplateActive}
        isActivating={isTemplateActivating}
        templateStatus={templateStatus}
        onToggleActive={() => handleChangeIsActive(!isTemplateActive)}
        onRun={handleRunProcess}
      />
    </>
  );
}
