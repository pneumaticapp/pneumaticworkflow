/* eslint-disable */
/* prettier-ignore */
import { convertEnumToObject } from '../helpers';
import { ERoutes } from '../../constants/routes';
import { TITLES } from '../../constants/titles';
import { getBrowserConfig } from '../getConfig';
import { removePneumaticSuffix } from '../strings';

export const getAnalyticsId = () => {
  const { config: { analyticsId } } = getBrowserConfig();

  return analyticsId;
};

export const getAnalyticsPageParams = (pathname: string, search?: string) => {
  const isWorkflowsInWork = [
    pathname.includes(ERoutes.Workflows) && !search,
    pathname.includes(ERoutes.Workflows) && search?.includes('type=workflows-in-work'),
  ].some(Boolean);
  const isWorkflowsDelayed = [
    pathname.includes(ERoutes.Workflows),
    search?.includes('type=workflows-delayed'),
  ].every(Boolean);
  const isWorkflowsCompleted = [
    pathname.includes(ERoutes.Workflows),
    search?.includes('type=workflows-completed'),
  ].every(Boolean);
  const isTemplatesEdit = pathname.includes(ERoutes.TemplatesEdit.replace(':id/', ''));
  const isTemplatesCreate = pathname.includes(ERoutes.TemplatesCreate);
  const isTemplates = pathname.includes(ERoutes.Templates);
  const taskDetailRegExp = /\/tasks\/\d+/i;
  const isTaskDetail = taskDetailRegExp.test(pathname);

  const guestTaskRegExp = /\/guest-task\/\d+/i;
  const isGuestTask = guestTaskRegExp.test(pathname);
  // Next hardcoded analytics params should be removed
  // after we will be sure, that rename from processes -> workflows
  // and from workflows -> templates was successfull.
  const SPECIFIC_CASES = [
    {
      check: isWorkflowsInWork,
      analyticsParams: ['Workflows In Progress', { title: TITLES.Workflows }],
    },
    {
      check: isWorkflowsDelayed,
      analyticsParams: ['Delayed Workflows', { title: TITLES.Workflows }],
    },
    {
      check: isWorkflowsCompleted,
      analyticsParams: ['Completed Workflows', { title: TITLES.Workflows }],
    },
    {
      check: isTaskDetail,
      analyticsParams: [removePneumaticSuffix(TITLES.TasksDetail), { title: TITLES.TasksDetail }],
    },
    {
      check: isGuestTask,
      analyticsParams: [removePneumaticSuffix(TITLES.TasksDetail), { title: TITLES.TasksDetail }],
    },
    {
      check: isTemplatesEdit,
      analyticsParams: ['Edit Workflow', { title: TITLES.TemplatesEdit }],
    },
    {
      check: isTemplatesCreate,
      analyticsParams: ['Add Workflow', { title: TITLES.TemplatesCreate }],
    },
    {
      check: isTemplates,
      analyticsParams: ['Workflows', { title: TITLES.Templates }],
    },
  ];

  const specificCaseParams = SPECIFIC_CASES.find(({ check }) => check)?.analyticsParams;

  if (specificCaseParams) {
    return specificCaseParams;
  }

  const analyticsInfo = ANALYTICS_ROUTES_TITLES_MAP[pathname];

  if (!analyticsInfo) {
    return [];
  }

  const isLegacy = analyticsInfo.name.includes('templates');

  if (isLegacy) {

  }
  const { category, name, title } = analyticsInfo;

  return [category, name, { title }];
};

const normalizedRoutes = convertEnumToObject(ERoutes);
const normalizedTitles = convertEnumToObject(TITLES);

export interface IAnalyticsRoutesTitlesMap {
  [route: string]: {
    name: string;
    title: string;
    category?: string;
  } | undefined;
}

export const ANALYTICS_CATEGORIES: string[] = [];

export const ANALYTICS_ROUTES_TITLES_MAP: IAnalyticsRoutesTitlesMap = Object.keys(normalizedRoutes)
  .reduce((acc, key) => {
    const route = normalizedRoutes[key].replace(':id/', '');
    const title = normalizedTitles[key];

    if (!title) {
      return acc;
    }

    const name = removePneumaticSuffix(title);
    const category = ANALYTICS_CATEGORIES.find(category => name.toLowerCase().includes(category.toLowerCase()));

    return { ...acc, [route]: { category, name, title }};
  }, {});
