import React, { useContext, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { WarningIcon } from '../../icons';
import { ITemplateClient } from '../../../types/template';
import {
  cloneTemplate,
  deleteTemplate,
  discardTemplateChanges,
  openRunWorkflowModal,
  patchTemplate,
} from '../../../redux/actions';
import { getRunnableWorkflow, loadDatasetsMap } from '../utils/getRunnableWorkflow';
import { mapFieldsetBindingClientToRuntime } from '../../../utils/mapFieldsetBindingClientToRuntime';
import { ETemplateStatus, IApplicationState } from '../../../types/redux';
import { validateTemplate } from '../utils/validateTemplate';
import { isArrayWithItems } from '../../../utils/helpers';
import { NotificationManager } from '../../UI/Notifications';
import { history } from '../../../utils/history';
import { useTemplateIntegrationsList } from '../../TemplateIntegrationsStats';
import { checkShowDraftTemplateWarning } from '../../Templates';

import styles from './TemplateControlls.css';
import { ESubscriptionPlan } from '../../../types/account';
import { TemplateFieldContext, TemplatePersistContext } from '../useTemplateForm/contexts';
import { ITemplateControllsProps } from './types';
import {
  TemplateControlButtons,
  TemplateMoreSettings,
  TemplateNotificationSettings,
  TemplateOwnersSettings,
} from './TemplateControlsSections';
import { TemplateNavigation } from './TemplateNavigation';
export type { ITemplateControllsProps } from './types';

export function TemplateControlls({
  template: propsTemplate,
  templateStatus: propsTemplateStatus,
  isSubscribed: propsIsSubscribed,
  cloneTemplate: propsCloneTemplate,
  patchTemplate: propsPatchTemplate,
  deleteTemplate: propsDeleteTemplate,
  openRunWorkflowModal: propsOpenRunWorkflowModal,
  setInfoWarnings,
}: ITemplateControllsProps) {
  const intl = useIntl();
  const { formatMessage } = intl;
  const dispatch = useDispatch();
  const fieldContext = useContext(TemplateFieldContext);
  const persistContext = useContext(TemplatePersistContext);
  const template = propsTemplate ?? fieldContext?.values;
  const setFieldValue = fieldContext?.setFieldValue ?? (() => undefined);
  const {
    consumePendingChanges,
    confirmConsumedChanges,
    revertConsumedChanges,
    abandonPendingChanges,
  } = persistContext ?? {
    consumePendingChanges: (explicitFields = {}) => explicitFields,
    confirmConsumedChanges: () => undefined,
    revertConsumedChanges: () => undefined,
    abandonPendingChanges: () => undefined,
  };
  const templateStatusFromState = useSelector((state: IApplicationState) => state.template?.status ?? ETemplateStatus.Saved);
  const isSubscribedFromState = useSelector((state: IApplicationState) => state.authUser?.account?.isSubscribed ?? false);
  const billingPlanFromState = useSelector((state: IApplicationState) => state.authUser?.account?.billingPlan);
  const templateStatus = propsTemplateStatus ?? templateStatusFromState;
  const isSubscribed = propsIsSubscribed ?? isSubscribedFromState;

  if (!template) {
    throw new Error('TemplateControlls must receive a template prop or be used inside the Edit Template form provider');
  }
  const isFreePlan = billingPlanFromState === ESubscriptionPlan.Free;
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

  const runCloneTemplate = (payload: Parameters<typeof cloneTemplate>[0]) => {
    propsCloneTemplate ? propsCloneTemplate(payload) : dispatch(cloneTemplate(payload));
  };

  const runPatchTemplate = (payload: Parameters<typeof patchTemplate>[0]) => {
    propsPatchTemplate ? propsPatchTemplate(payload) : dispatch(patchTemplate(payload));
  };

  const runDeleteTemplate = (payload: Parameters<typeof deleteTemplate>[0]) => {
    propsDeleteTemplate ? propsDeleteTemplate(payload) : dispatch(deleteTemplate(payload));
  };

  const runOpenWorkflowModal = (payload: Parameters<typeof openRunWorkflowModal>[0]) => {
    propsOpenRunWorkflowModal ? propsOpenRunWorkflowModal(payload) : dispatch(openRunWorkflowModal(payload));
  };

  const handleRunProcess = async () => {
    const loadedFieldsets = template.kickoff.fieldsets.map(mapFieldsetBindingClientToRuntime);
    const datasetsMap = await loadDatasetsMap(template.kickoff, loadedFieldsets);
    const runnableWorkflow = getRunnableWorkflow(template, datasetsMap, loadedFieldsets);
    if (runnableWorkflow) {
      runOpenWorkflowModal(runnableWorkflow);
    }
  };

  const handleChangeIsActive = (value: ITemplateClient['isActive'], redirectUrl?: string) => {
    if (!value) {
      const pendingChanges = consumePendingChanges({ isActive: false });

      runPatchTemplate({
        changedFields: { ...pendingChanges, isActive: false },
        onSuccess: confirmConsumedChanges,
        onFailed: revertConsumedChanges,
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

    const pendingChanges = consumePendingChanges({ isActive: true });

    runPatchTemplate({
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
    });
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
            runDeleteTemplate({ templateId });
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
        onClone={() => templateId && runCloneTemplate({ templateId })}
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
