import {
  EUserListSorting,
  EUserStatus,
  IUnsavedUser,
  TGoogleAuthUserInfo,
  TUserListItem,
} from './user';
import { TNotificationsListItem } from './notifications';
import { IAccountGenericTemplate } from './genericTemplates';
import {
  ETemplatesSorting,
  EWorkflowsLogSorting,
  IWorkflowDetails,
  IWorkflowLogItem,
  IWorkflowEdit,
  IWorkflow,
  IWorkflowsSettings,
  EWorkflowsLoadingStatus,
} from './workflow';
import { ITask, ITaskListItem, ITasksSettings } from './tasks';
import { IIntegrationDetailed, IIntegrationListItem } from './integrations';
import { ESettingsTabs } from './profile';
import { IHighlightsItem, EHighlightsDateFilter } from './highlights';
import { EDashboardTimeRange, IGettingStartedChecklist } from './dashboard';
import { EAuthUserFailType, ETaskStatus, ETemplatesSystemStatus } from '../redux/actions';
import {
  ITemplate,
  ITemplateListItem,
  ISystemTemplate,
  ITemplateTitle,
  TTemplateIntegrationStats,
  TAITemplateGenerationStatus,
} from './template';
import { IRunWorkflow } from '../components/WorkflowEditPopup/types';
import { TTaskVariable } from '../components/TemplateEdit/types';
import { ETaskListStatus } from '../components/Tasks/types';
import { ESubscriptionPlan } from './account';
import { IMenuItem } from './menu';
import { EWebhooksTypeEvent, IWebhook } from './webhooks';
import { ETenantsSorting, ITenant } from './tenants';
import { IPagesStore } from './page';
import { IOAuthInviteView, IUserInviteMicrosoft } from './team';

export interface IApplicationState {
  general: IGeneralStore;
  accounts: IAccounts;
  genericTemplates: IGenericTemplatesStore;
  authUser: IAuthUser;
  dashboard: IDashboardStore;
  menu: IMenu;
  settings: ISettings;
  notifications: IStoreNotification;
  workflows: IStoreWorkflows;
  task: IStoreTask;
  profile: IStoreProfile;
  teamInvites: ITeamInvitesStore;
  highlights: IHighlightsStore;
  templates: ITemplatesStore;
  selectTemplateModal: ISelectTemplateModalStore;
  template: ITemplateStore;
  integrations: IIntegrationsStore;
  runWorkflowModal: IStoreRunWorkflowModal;
  tasks: IStoreTasks;
  buyPlanModal: IBuyPlanModalStore;
  webhooks: IWebhookStore;
  tenants: ITenantsStore;
  pages: IPagesStore;
}

export enum ELoggedState {
  LoggedIn = 'logged-in',
  LoggedOut = 'logged-out',
}

export interface IAuthUser extends IUnsavedUser {
  error?: EAuthUserFailType;
  isSuperuser?: boolean;
  isSupermode?: boolean;
  superUserToken?: '';
  id: number;
  status: EUserStatus;
  loading: boolean;
  googleAuthUserInfo: TGoogleAuthUserInfo;
  invitedUser: IInvitedUser;
  isAccountOwner: boolean;
  isDigestSubscriber: boolean;
  isTasksDigestSubscriber: boolean;
  isCommentsMentionsSubscriber: boolean;
  isNewTasksSubscriber: boolean;
  isNewslettersSubscriber: boolean;
  isSpecialOffersSubscriber: boolean;
  loggedState: ELoggedState;
  language: string,
  timezone: string,
  dateFmt: string,
  dateFdw: string,
}

export interface IInvitedUser {
  id: string;
}

export interface IMenu {
  items: IMenuItem[];
  containerClassnames: string;
  subHiddenBreakpoint: number;
  menuHiddenBreakpoint: number;
  menuClickCount: number;
  selectedMenuHasSubItems: boolean;
}

export const enum ELocale {
  English = 'en',
  Russian = 'ru',
}

export const enum ELocaleDirection {
  LeftToRight = 'ltr',
  RightToLeft = 'rtl',
}

export interface ILocaleOption {
  id: ELocale;
  name: string;
  direction: ELocaleDirection;
}

export interface ISettings {
  locale: ELocale;
}

export interface IAccountPlan {
  planExpiration: string | null; // null for free plan
  maxUsers: number;
  activeUsers: number | null;
  tenantsActiveUsers: number | null;
  maxTemplates: number | null; // null for free plan
  activeTemplates: number;
  ownerName: string;
  trialEnded: boolean;
  billingPlan: ESubscriptionPlan;
  trialIsActive: boolean;
  isSubscribed: boolean;
}

export enum EDeleteUserModalState {
  Closed = 'closed',
  FetchingUserData = 'fetching-user-data',
  WaitingForAction = 'waiting-for-action',
  PerformingAction = 'performing-action',
}

export interface IAccounts {
  isLoading: boolean;
  planInfo: IAccountPlan;
  users: TUserListItem[];
  team: {
    list: TUserListItem[];
    isLoading: boolean;
  };
  userListSorting: EUserListSorting;
  deleteUserModal: {
    user: TUserListItem | null;
    userWorkflowsCount: number;
    state: EDeleteUserModalState;
  };
}

export interface IStoreTask {
  data: ITask | null;
  status: ETaskStatus;
}

export interface IGenericTemplatesStore {
  genericTemplates: IAccountGenericTemplate[];
  selected: number[];
  loading: boolean;
}

export interface IGeneralStore {
  isLoaderVisible: boolean;
  fullscreenImage: {
    isOpen: boolean;
    url: string;
  };
}

export interface IStoreNotification {
  items: TNotificationsListItem[];
  totalItemsCount: number;
  unreadItemsCount: number;
  isNotificationsListOpen: boolean;
  hasNewNotifications: boolean;
  isLoading: boolean;
}

export interface IIntegrationsStore {
  apiKey: {
    isLoading: boolean;
    data: string;
  };
  list: {
    isLoading: boolean;
    data: IIntegrationListItem[];
  };
  detailed: {
    isLoading: boolean;
    data: IIntegrationDetailed | null;
  };
}

export interface IStoreWorkflows {
  isUrgent: boolean;
  saving?: boolean;
  workflow: IWorkflowDetails | null;
  isWorkflowLoading: boolean;
  workflowEdit: IWorkflowEdit;
  workflowsSearchText: string;
  workflowLog: IWorkflowLog;
  workflowsList: IWorkflowsList;
  workflowsSettings: IWorkflowsSettings;
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
}

export interface IStoreTasks {
  taskList: ITaskList;
  taskListDetailedTaskId: number | null;
  tasksSearchText: string;
  tasksSettings: ITasksSettings;
  taskListStatus: ETaskListStatus;
  tasksCount: number | null;
  hasNewTasks: boolean;
}

export interface IWorkflowLog {
  items: IWorkflowLogItem[];
  isCommentsShown: boolean;
  isOnlyAttachmentsShown: boolean;
  sorting: EWorkflowsLogSorting;
  isOpen: boolean;
  workflowId: number | null;
  isLoading: boolean;
}

export interface ITemplatesSystemCategories {
  id: number;
  order: number;
  name: string;
  icon: string;
  color: string;
  templateColor: string;
}

export interface ITemplatesSystemSelection {
  count: number;
  offset: number;
  searchText: string;
  category: number | null;
}

export interface ITemplatesSystemList {
  items: ISystemTemplate[];
  selection: ITemplatesSystemSelection;
}

export interface ITemplatesSystem {
  isLoading: boolean;
  categories: ITemplatesSystemCategories[];
  list: ITemplatesSystemList;
  status: ETemplatesSystemStatus;
}

export interface ITemplatesStore {
  systemTemplates: ITemplatesSystem;
  isListLoading: boolean;
  templatesList: ITemplatesList;
  templatesListSorting: ETemplatesSorting;
  templatesVariablesMap: { [key in number]: TTaskVariable[] };
  templatesIntegrationsStats: { [key in number]: TTemplateIntegrationStats };
}

export interface IBuyPlanModalStore {
  isOpen: boolean;
  headerTextId: string;
}

export enum ETemplateStatus {
  Loading = 'loading',
  LoadingFailed = 'loading-failed',
  Saved = 'saved',
  Saving = 'saving',
  SaveFailed = 'save-failed',
  Sharing = 'Sharing',
  SaveCanceled = 'save-canceled',
}

export interface ITemplateStore {
  data: ITemplate;
  status: ETemplateStatus;
  AITemplate: {
    isModalOpened: boolean;
    generationStatus: TAITemplateGenerationStatus;
    generatedData: ITemplate | null;
  };
}

export interface ITemplatesList {
  count: number;
  offset: number;
  items: ITemplateListItem[];
}

export interface IWorkflowsList {
  count: number;
  offset: number;
  items: IWorkflow[];
}

export interface ITaskList {
  count: number;
  offset: number;
  items: ITaskListItem[];
}

export interface IStoreProfile {
  isLoading?: boolean;
  settingsTab: ESettingsTabs;
}

export type ITeamInvitesStore = {
  isInvitesPopupOpen: boolean;
  recentInvitedUsers: TUserListItem[];
  googleUsers: IOAuthInviteView[];
  microsoftUsers: IUserInviteMicrosoft[];
};

export type ITenantsStore = {
  list: ITenant[];
  isLoading: boolean;
  count: number | null;
  sorting: ETenantsSorting;
};

export type IWebhookStore = Record<EWebhooksTypeEvent, IWebhook>;

export interface IAction<Type> {
  type: Type;
}

export interface ITypedReduxAction<Type, Payload> extends IAction<Type> {
  payload: Payload;
}

export interface IDashboardCounters {
  completed: number;
  inProgress: number;
  overdue: number;
  started: number;
}

export interface IDashboardTask {
  id: number;
  number: number;
  name: string;
  started: number | null;
  inProgress: number;
  overdue: number;
  completed: number | null;
}

export type TDashboardBreakdownItemResponse = {
  templateId: number;
  templateName: string;
  started: number | null;
  inProgress: number;
  overdue: number;
  isActive?: boolean;
  completed: number | null;
};

export type TDashboardBreakdownItem = TDashboardBreakdownItemResponse & {
  tasks: IDashboardTask[];
  areTasksLoading: boolean;
};

export enum EDashboardModes {
  Workflows = 'dashboard.workflows',
  Tasks = 'dashboard.tasks',
}

export interface IDashboardStore {
  counters: IDashboardCounters;
  timeRange: EDashboardTimeRange;
  breakdownItems: TDashboardBreakdownItem[];
  mode: EDashboardModes;
  isLoading: boolean;
  settingsChanged: boolean;
  checklist: {
    isLoading: boolean;
    isCompleted: boolean;
    checks: IGettingStartedChecklist;
  };
}

export interface IHighlightsFilters {
  timeRange: EHighlightsDateFilter;
  startDate: Date;
  endDate: Date;
  usersFilter: number[];
  templatesFilter: number[];
  filtersChanged: boolean;
}

export interface IHighlightsStore {
  count: number;
  isFeedLoading: boolean;
  isUsersLoading: boolean;
  isTemplatesTitlesLoading: boolean;
  items: IHighlightsItem[];
  templatesTitles: ITemplateTitle[];
  filters: IHighlightsFilters;
}

export interface ISelectTemplateModalStore {
  isOpen: boolean;
  ancestorTaskId: number | null;
  isLoading: boolean;
  items: ITemplateListItem[];
  templatesIdsFilter: number[];
}

export interface IStoreRunWorkflowModal {
  workflow: IRunWorkflow | null;
  isOpen: boolean;
  isWorkflowStarting: boolean;
}
