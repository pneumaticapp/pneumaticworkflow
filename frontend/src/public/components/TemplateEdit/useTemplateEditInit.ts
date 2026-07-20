import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { FormikProps } from 'formik';

import { ITemplateEditParams } from './types';
import { createEmptyTemplate } from './utils/createTemplateEditTask';
import { getVariables } from './TaskForm/utils/getTaskVariables';
import { ERoutes } from '../../constants/routes';
import { getNormalizedTemplateOwners, getTemplateIdFromUrl } from '../../utils/template';
import { checkSomeRouteIsActive, isCreateTemplate } from '../../utils/history';
import { usePrevious } from '../../hooks/usePrevious';
import { ITemplateClient } from '../../types/template';
import { TUserListItem } from '../../types/user';
import {
  loadTemplate,
  loadTemplateFromSystem,
  loadTemplateVariablesSuccess,
  resetTemplateStore,
  saveTemplate,
  setTemplate,
} from '../../redux/actions';
import { IAuthUser } from '../../types/redux';
import { getTemplateVariablesFingerprint } from './useTemplateForm/templateFormUtils';

const TEMPLATE_VARIABLES_SYNC_DEBOUNCE_MS = 350;

type TUseTemplateEditInitParams = {
  match: { params: ITemplateEditParams };
  location: { pathname: string; search: string };
  template: ITemplateClient;
  aiTemplate: ITemplateClient | null;
  users: TUserListItem[];
  accessConditions: boolean;
  authUser: IAuthUser;
  formik: FormikProps<ITemplateClient>;
  openTask(taskUUID?: string): void;
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
}: TUseTemplateEditInitParams) {
  const dispatch = useDispatch();
  const prevUsers = usePrevious(users);
  const prevLocation = usePrevious(location);
  const prevTemplate = usePrevious(template);
  const lastVariablesTemplateIdRef = useRef<number | null>(null);
  const formikValuesRef = useRef(formik.values);
  formikValuesRef.current = formik.values;

  const variablesFingerprint = getTemplateVariablesFingerprint(formik.values);

  const initPage = () => {
    const { id } = match.params;
    const workflowTemplateId = getTemplateIdFromUrl(location.search);
    const isCreateWorflowPage = isCreateTemplate();
    const isEditWorkflow = Boolean(id);
    const initMap = [
      {
        check: isCreateWorflowPage && workflowTemplateId,
        init: () => dispatch(loadTemplateFromSystem(workflowTemplateId!)),
      },
      {
        check: checkSomeRouteIsActive(ERoutes.TemplatesCreateAI),
        init: () => {
          const templateLocal = aiTemplate || createEmptyTemplate(authUser, users, accessConditions);
          dispatch(setTemplate(templateLocal));
          dispatch(saveTemplate());
        },
      },
      {
        check: isCreateWorflowPage && !workflowTemplateId,
        init: () => dispatch(setTemplate(createEmptyTemplate(authUser, users, accessConditions))),
      },
      {
        check: isEditWorkflow,
        init: () => dispatch(loadTemplate(Number(id))),
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
      dispatch(resetTemplateStore());
    };
  }, []);

  const firstTaskUuid = formik.values.tasks[0]?.uuid;

  useEffect(() => {
    if (checkSomeRouteIsActive(ERoutes.TemplatesCreate) || checkSomeRouteIsActive(ERoutes.TemplatesCreateAI)) {
      openTask(firstTaskUuid);
    }
  }, [firstTaskUuid, location.pathname, openTask]);

  useEffect(() => {
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
    }
  }, [location, template]);

  useEffect(() => {
    if (users.length === prevUsers?.length) {
      return;
    }

    // Build from the current Formik values, not the Redux `template` prop.
    // Field edits live in Formik until `TemplateFormPersistProvider` flushes
    // them to Redux, so the Redux snapshot can lag behind. Formik uses
    // `enableReinitialize`, so a `setTemplate` built from the stale Redux
    // prop would reset Formik to that snapshot and discard any uncommitted
    // edits. Spreading from `formik.values` carries those edits into the
    // new Redux state so the reinitialize is a no-op for them.
    const currentValues = formikValuesRef.current;
    const newTemplateOwners = getNormalizedTemplateOwners(currentValues.owners, accessConditions, users);
    dispatch(setTemplate({ ...currentValues, owners: newTemplateOwners }));
  }, [users, accessConditions, prevUsers?.length, dispatch]);

  useEffect(() => {
    const syncVariables = () => {
      const currentValues = formikValuesRef.current;

      if (currentValues.id) {
        dispatch(loadTemplateVariablesSuccess({
          templateId: currentValues.id,
          variables: getVariables({
            kickoff: currentValues.kickoff,
            tasks: currentValues.tasks,
            templateId: currentValues.id,
          }),
        }));
      }
    };

    // Populate immediately whenever the persisted template identity changes.
    // Subsequent metadata edits within that template remain debounced.
    const currentTemplateId = formikValuesRef.current.id ?? null;
    if (lastVariablesTemplateIdRef.current !== currentTemplateId) {
      lastVariablesTemplateIdRef.current = currentTemplateId;
      syncVariables();
      return undefined;
    }

    const timeoutId = window.setTimeout(syncVariables, TEMPLATE_VARIABLES_SYNC_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [variablesFingerprint, dispatch]);
}
