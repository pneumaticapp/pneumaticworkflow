import * as React from 'react';
import { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RouteComponentProps } from 'react-router-dom';

import { ERoutes } from '../../constants/routes';
import { TUserListItem } from '../../types/user';
import { getNormalizedTemplateOwners, getTemplateIdFromUrl } from '../../utils/template';
import { checkSomeRouteIsActive, isCreateTemplate } from '../../utils/history';
import { ITemplateClient } from '../../types/template';
import { TLoadTemplateVariablesSuccessPayload } from '../../redux/actions';
import { ETemplateStatus, IAuthUser } from '../../types/redux';
import { usePrevious } from '../../hooks/usePrevious';
import { getSubscriptionPlan } from '../../redux/selectors/user';
import { getIsCatalogLoaded } from '../../redux/selectors/fieldsets';
import { loadFieldsetsCatalog } from '../../redux/fieldsets/slice';
import { ESubscriptionPlan } from '../../types/account';
import { EGraphViewMode } from './TemplateGraphEditor';
import { resetGraphView, setViewMode } from '../../redux/templateGraphView/slice';
import { TemplateEditVariablesSync } from './TemplateEditVariablesSync';
import { createEmptyTemplate } from './utils/createEmptyTemplate';
import { getGraphShowcaseTemplate } from './TemplateGraphEditor/fixtures/graphShowcaseTemplate';
import { getGraphWeaveTemplate } from './TemplateGraphEditor/fixtures/graphWeaveTemplate';
import { TemplateEditorContainer } from './TemplateEditorContainer/TemplateEditorContainer';

export interface ITemplateEditProps {
  authUser: IAuthUser;
  template: ITemplateClient;
  aiTemplate: ITemplateClient | null;
  templateStatus: ETemplateStatus;
  users: TUserListItem[];
  isSubscribed: boolean;
  loadTemplate(id: number): void;
  loadTemplateFromSystem(id: string): void;
  resetTemplateStore(): void;
  saveTemplate(): void;
  setTemplate(payload: ITemplateClient): void;
  setTemplateStatus(status: ETemplateStatus): void;
  loadTemplateVariablesSuccess(payload: TLoadTemplateVariablesSuccessPayload): void;
}

export interface ITemplateEditParams {
  id: string;
}

export type TTemplateEditProps = ITemplateEditProps & RouteComponentProps<ITemplateEditParams>;

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
  setTemplateStatus,
  loadTemplateVariablesSuccess,
}: TTemplateEditProps) {
  const dispatch = useDispatch();
  const { owners } = template;
  const billingPlan = useSelector(getSubscriptionPlan);
  const isCatalogLoaded = useSelector(getIsCatalogLoaded);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;
  const prevUsers = usePrevious(users);
  const prevLocation = usePrevious(location);
  const prevTemplate = usePrevious(template);

  const getEmptyTemplate = (): ITemplateClient => createEmptyTemplate({ authUser, accessConditions, users });

  const initPage = (): void => {
    const { id } = match.params;
    const workflowTemplateId = getTemplateIdFromUrl(location.search);
    const isCreateWorkflowPage = isCreateTemplate();
    const isEditWorkflow = Boolean(id);
    const initMap = [
      {
        check: isCreateWorkflowPage && workflowTemplateId,
        init: () => loadTemplateFromSystem(workflowTemplateId as string),
      },
      {
        check: checkSomeRouteIsActive(ERoutes.TemplatesCreateAI),
        init: () => {
          setTemplate(aiTemplate || getEmptyTemplate());
          saveTemplate();
        },
      },
      {
        check: isCreateWorkflowPage && !workflowTemplateId,
        init: () => {
          const emptyTemplate = getEmptyTemplate();
          const showcase = new URLSearchParams(location.search).get('showcase');
          const isGraphShowcase = showcase === 'graph' || showcase === 'graph-weave';

          if (!isGraphShowcase) {
            setTemplate(emptyTemplate);
            return;
          }

          const showcaseTemplate =
            showcase === 'graph-weave' ? getGraphWeaveTemplate(emptyTemplate) : getGraphShowcaseTemplate(emptyTemplate);
          setTemplate(showcaseTemplate);
          dispatch(setViewMode(EGraphViewMode.Graph));
        },
      },
      {
        check: isEditWorkflow,
        init: () => loadTemplate(Number(id)),
      },
    ];

    initMap.find(({ check }) => check)?.init();
  };

  const lifecycleRef = useRef({
    dispatch,
    initPage,
    isCatalogLoaded,
    resetTemplateStore,
  });

  useEffect(() => {
    const lifecycle = lifecycleRef.current;
    lifecycle.initPage();

    if (!lifecycle.isCatalogLoaded) {
      lifecycle.dispatch(loadFieldsetsCatalog());
    }

    return () => {
      lifecycle.resetTemplateStore();
      lifecycle.dispatch(resetGraphView());
    };
  }, []);

  const pageUpdateRef = useRef({
    accessConditions,
    initPage,
    location,
    owners,
    setTemplate,
    template,
    users,
  });
  pageUpdateRef.current = {
    accessConditions,
    initPage,
    location,
    owners,
    setTemplate,
    template,
    users,
  };

  useEffect(() => {
    const current = pageUpdateRef.current;
    const pathName = current.location.pathname;
    const prevPathName = prevLocation?.pathname;
    const isPreviousPathCreate = prevPathName === ERoutes.TemplatesCreate;
    const isCurrentPathEdit = checkSomeRouteIsActive(ERoutes.TemplatesEdit);
    const isCreateScenario = isPreviousPathCreate && isCurrentPathEdit;
    const isLocationChanged = pathName !== prevPathName;
    const isFirstRender = !prevLocation && !prevTemplate && !prevUsers;

    if (!isCreateScenario && isLocationChanged) {
      if (!isFirstRender) current.initPage();
      return;
    }

    if (current.users.length !== prevUsers?.length) {
      const normalizedOwners = getNormalizedTemplateOwners(current.owners, current.accessConditions, current.users);
      current.setTemplate({ ...current.template, owners: normalizedOwners });
    }
  }, [prevTemplate, prevLocation, prevUsers]);

  if (templateStatus === ETemplateStatus.Loading) {
    return <div className="loading" />;
  }

  const shouldOpenFirstTask =
    checkSomeRouteIsActive(ERoutes.TemplatesCreate) || checkSomeRouteIsActive(ERoutes.TemplatesCreateAI);

  return (
    <>
      <TemplateEditVariablesSync
        template={template}
        prevTemplate={prevTemplate}
        loadTemplateVariablesSuccess={loadTemplateVariablesSuccess}
      />
      <TemplateEditorContainer
        template={template}
        authUser={authUser}
        users={users}
        isSubscribed={isSubscribed}
        accessConditions={accessConditions}
        shouldOpenFirstTask={shouldOpenFirstTask}
        saveTemplate={saveTemplate}
        setTemplate={setTemplate}
        setTemplateStatus={setTemplateStatus}
      />
    </>
  );
}
