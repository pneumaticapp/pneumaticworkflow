import { IMenuItem, TMenuCounterType } from '../types/menu';
import {
  DashboardIcon,
  InboxIcon,
  WorkflowsIcon,
  TaskAcivityIcon,
  TeamIcon,
  TemplatesIcon,
  IntegrationsIcon,
  TenantsIcon,
} from '../components/icons';

import { ERoutes } from './routes';
import { HelpIcon } from '../components/icons/HelpIcon';
import { IAuthUser } from '../types/redux';
import { ESubscriptionPlan } from '../types/account';

export type TMenuCounter = {
  id: IMenuItem['id'];
  value: number;
  type: TMenuCounterType;
};

export const getUserMenuItems = (user: IAuthUser, counters?: TMenuCounter[]): IMenuItem[] => {
  const items: IMenuItem[] = [
    {
      id: 'dashboards',
      iconComponent: DashboardIcon,
      label: 'menu.dashboard',
      to: ERoutes.Main,
    },
    {
      id: 'tasks',
      iconComponent: InboxIcon,
      label: 'menu.tasks',
      to: ERoutes.Tasks,
    },
    {
      id: 'workflows',
      iconComponent: WorkflowsIcon,
      label: 'menu.workflows',
      to: ERoutes.Workflows,
      isHidden: !user.isAdmin,
    },
    {
      id: 'templates',
      iconComponent: TemplatesIcon,
      label: 'menu.templates',
      to: ERoutes.Templates,
      isHidden: !user.isAdmin,
    },
    {
      id: 'highlights',
      iconComponent: TaskAcivityIcon,
      label: 'menu.highlights',
      to: ERoutes.Highlights,
      isHidden: !user.isAdmin,
    },
    {
      id: 'team',
      iconComponent: TeamIcon,
      label: 'menu.team',
      to: ERoutes.Team,
      isHidden: !user.isAdmin,
    },
    {
      id: 'integrations',
      to: ERoutes.Integrations,
      label: 'menu.integrations',
      iconComponent: IntegrationsIcon,
      isHidden: !user.isAdmin,
    },
    {
      id: 'help-center',
      to: 'https://support.pneumatic.app/en/',
      label: 'menu.help-center',
      subsSlug: 'help-center',
      newWindow: true,
      iconComponent: HelpIcon,
    },
    {
      id: 'tenants',
      to: ERoutes.Tenants,
      label: 'menu.tenants',
      iconComponent: TenantsIcon,
      isHidden: !user.isAdmin || user.account.billingPlan === ESubscriptionPlan.Free || user.account.leaseLevel === 'tenant',
    },
  ];

  const itemsWithCounters: IMenuItem[] = items.map((item) => {
    if (!counters) {
      return item;
    }
    const counter = counters?.find((counter) => counter.id === item.id);

    return counter ? { ...item, counter: counter.value, counterType: counter.type } : item;
  });

  return itemsWithCounters;
};
