import React, { useRef } from 'react';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';

import { TemplateEditLayout } from './TemplateEditLayout';
import { useTemplateEditInit } from './useTemplateEditInit';
import { useTemplateEditTasks } from './useTemplateEditTasks';
import { getSubscriptionPlan } from '../../redux/selectors/user';
import { ESubscriptionPlan } from '../../types/account';
import { ETemplateStatus } from '../../types/redux';
import { TemplateForm, useTemplateForm } from './useTemplateForm';
import { resolveTemplateFormIdentity } from './useTemplateForm/templateFormUtils';

import { TTemplateEditProps } from './templateEditPage.types';

export * from './templateEditPage.types';

export function TemplateEdit({
  match,
  location,
  authUser,
  template,
  aiTemplate,
  templateStatus,
  users,
  isSubscribed,
  loadTemplate,
  loadTemplateFromSystem,
  resetTemplateStore,
  saveTemplate,
  setTemplate,
  loadTemplateVariablesSuccess,
}: TTemplateEditProps) {
  const { formatMessage } = useIntl();
  const templateIdentity = resolveTemplateFormIdentity(template, location);
  const createSessionKeyRef = useRef<string | undefined>(undefined);

  if (!template.id && typeof templateIdentity === 'string') {
    createSessionKeyRef.current = templateIdentity;
  }

  const templateFormKey = template.id ?? createSessionKeyRef.current ?? 'create';
  const { formik, setFieldValue, setValues, dirtyRef, pendingUserEditsRef, persistBaselineSyncRef } = useTemplateForm(
    template,
    templateIdentity,
  );
  const billingPlan = useSelector(getSubscriptionPlan);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;

  const { sortedTasks, handleAddTask, getTaskListItem, openTask } = useTemplateEditTasks({
    authUser,
    formik,
    setFieldValue,
    users,
    accessConditions,
    formatMessage,
    isSubscribed,
  });

  useTemplateEditInit({
    match,
    location,
    template,
    aiTemplate,
    users,
    accessConditions,
    authUser,
    formik,
    openTask,
    loadTemplate,
    loadTemplateFromSystem,
    resetTemplateStore,
    saveTemplate,
    setTemplate,
    loadTemplateVariablesSuccess,
  });

  if (templateStatus === ETemplateStatus.Loading) {
    return <div className="loading" />;
  }

  return (
    <TemplateForm
      key={templateFormKey}
      formik={formik}
      setFieldValue={setFieldValue}
      setValues={setValues}
      dirtyRef={dirtyRef}
      pendingUserEditsRef={pendingUserEditsRef}
      persistBaselineSyncRef={persistBaselineSyncRef}
    >
      <TemplateEditLayout
        accessConditions={accessConditions}
        sortedTasks={sortedTasks}
        getTaskListItem={getTaskListItem}
        handleAddTask={handleAddTask}
      />
    </TemplateForm>
  );
}
