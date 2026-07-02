import { useEffect } from 'react';
import { FormikProps } from 'formik';

import { ITemplateEditParams } from './templateEditPage.types';
import { createEmptyTemplate } from './utils/createTemplateEditTask';
import { getVariables } from './TaskForm/utils/getTaskVariables';
import { ERoutes } from '../../constants/routes';
import { getNormalizedTemplateOwners, getTemplateIdFromUrl } from '../../utils/template';
import { checkSomeRouteIsActive, isCreateTemplate } from '../../utils/history';
import { usePrevious } from '../../hooks/usePrevious';
import { ITemplate } from '../../types/template';
import { TUserListItem } from '../../types/user';
import { TLoadTemplateVariablesSuccessPayload } from '../../redux/actions';
import { IAuthUser } from '../../types/redux';

type TUseTemplateEditInitParams = {
  match: { params: ITemplateEditParams };
  location: { pathname: string; search: string };
  template: ITemplate;
  aiTemplate: ITemplate | null;
  users: TUserListItem[];
  accessConditions: boolean;
  authUser: IAuthUser;
  formik: FormikProps<ITemplate>;
  openTask(taskUUID?: string): void;
  loadTemplate(id: number): void;
  loadTemplateFromSystem(id: string): void;
  resetTemplateStore(): void;
  saveTemplate(): void;
  setTemplate(payload: ITemplate): void;
  loadTemplateVariablesSuccess(payload: TLoadTemplateVariablesSuccessPayload): void;
};

export function useTemplateEditInit({
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
}: TUseTemplateEditInitParams) {
  const prevUsers = usePrevious(users);
  const prevLocation = usePrevious(location);
  const prevTemplate = usePrevious(template);
  const prevFormikValues = usePrevious(formik.values);

  const initPage = () => {
    const { id } = match.params;
    const workflowTemplateId = getTemplateIdFromUrl(location.search);
    const isCreateWorflowPage = isCreateTemplate();
    const isEditWorkflow = Boolean(id);
    const initMap = [
      {
        check: isCreateWorflowPage && workflowTemplateId,
        init: () => loadTemplateFromSystem(workflowTemplateId!),
      },
      {
        check: checkSomeRouteIsActive(ERoutes.TemplatesCreateAI),
        init: () => {
          const templateLocal = aiTemplate || createEmptyTemplate(authUser, users, accessConditions);
          setTemplate(templateLocal);
          saveTemplate();
        },
      },
      {
        check: isCreateWorflowPage && !workflowTemplateId,
        init: () => setTemplate(createEmptyTemplate(authUser, users, accessConditions)),
      },
      {
        check: isEditWorkflow,
        init: () => loadTemplate(Number(id)),
      },
    ];
    const currentPageInit = initMap.find(({ check }) => check);

    if (currentPageInit) {
      currentPageInit.init();
    }
  };

  useEffect(() => {
    initPage();

    return () => {
      resetTemplateStore();
    };
  }, []);

  const firstTaskUuid = formik.values.tasks[0]?.uuid;

  useEffect(() => {
    if (checkSomeRouteIsActive(ERoutes.TemplatesCreate) || checkSomeRouteIsActive(ERoutes.TemplatesCreateAI)) {
      openTask(firstTaskUuid);
    }
  }, [firstTaskUuid, location.pathname, openTask]);

  useEffect(() => {
    // Derive variables from Formik, not the Redux `template` prop. Kickoff/task
    // field edits update Formik immediately while Redux stays stale until autosave.
    const variables = getVariables(formik.values);
    const prevVariables = prevFormikValues ? getVariables(prevFormikValues) : [];
    if (variables.length !== prevVariables.length) {
      if (formik.values.id) {
        loadTemplateVariablesSuccess({ templateId: formik.values.id, variables });
      }
    }

    const [pathName, prevPathName] = [location.pathname, prevLocation?.pathname];
    const isPreviousPathIsCreate = prevPathName === ERoutes.TemplatesCreate;
    const isCurrentPathIsEdit = checkSomeRouteIsActive(ERoutes.TemplatesEdit);
    const isCreateScenario = isPreviousPathIsCreate && isCurrentPathIsEdit;
    const isLocationChanged = pathName !== prevPathName;

    const isFirstRender = !prevLocation && !prevTemplate && !prevUsers;
    if (!isCreateScenario && isLocationChanged) {
      if (!isFirstRender) {
        initPage();
      }
      return;
    }

    if (users.length !== prevUsers?.length) {
      // Build from the current Formik values, not the Redux `template` prop.
      // Field edits live in Formik until `TemplateFormPersistProvider` flushes
      // them to Redux, so the Redux snapshot can lag behind. Formik uses
      // `enableReinitialize`, so a `setTemplate` built from the stale Redux
      // prop would reset Formik to that snapshot and discard any uncommitted
      // edits. Spreading from `formik.values` carries those edits into the
      // new Redux state so the reinitialize is a no-op for them.
      const newTemplateOwners = getNormalizedTemplateOwners(formik.values.owners, accessConditions, users);
      setTemplate({ ...formik.values, owners: newTemplateOwners });
    }
  }, [location, users, template, formik.values]);
}
