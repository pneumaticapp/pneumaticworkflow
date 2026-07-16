import React, { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';

import { TemplateEditLayout } from './TemplateEditLayout';
import { useTemplateEditInit } from './useTemplateEditInit';
import { useTemplateEditTasks } from './useTemplateEditTasks';
import { getCurrentUser } from '../../redux/selectors/authUser';
import { getNotDeletedAccountsUsers } from '../../redux/selectors/accounts';
import { getIsUserSubsribed, getSubscriptionPlan } from '../../redux/selectors/user';
import { getAITemplate, getTemplateData, getTemplateStatus } from '../../redux/selectors/template';
import { getIsCatalogLoaded } from '../../redux/selectors/fieldsets';
import { loadFieldsetsCatalog } from '../../redux/fieldsets/slice';
import { ESubscriptionPlan } from '../../types/account';
import { ETemplateStatus } from '../../types/redux';
import { TemplateForm, useTemplateForm } from './useTemplateForm';
import { resolveTemplateFormIdentity } from './useTemplateForm/templateFormUtils';

import { TTemplateEditProps } from './types';

export function TemplateEdit({
  match,
  location,
}: TTemplateEditProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const authUser = useSelector(getCurrentUser);
  const users = useSelector(getNotDeletedAccountsUsers);
  const template = useSelector(getTemplateData);
  const aiTemplate = useSelector(getAITemplate);
  const templateStatus = useSelector(getTemplateStatus);
  const isSubscribed = useSelector(getIsUserSubsribed);
  const isCatalogLoaded = useSelector(getIsCatalogLoaded);
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

  useEffect(() => {
    if (!isCatalogLoaded) {
      dispatch(loadFieldsetsCatalog());
    }
  }, [dispatch, isCatalogLoaded]);

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
