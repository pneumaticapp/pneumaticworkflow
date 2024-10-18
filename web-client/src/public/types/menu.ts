/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TMenuCounterType = 'alert' | 'info';

export type TMenuItemId = 'dashboards'
| 'tasks'
| 'workflows'
| 'templates'
| 'highlights'
| 'team'
| 'integrations'
| 'help-center'
| 'tenants';

export interface IMenuItem extends IMenuItemSub {
  counter?: number;
  counterType?: TMenuCounterType;
  subs?: IMenuItemSub[];
  subsSlug?: string;
}

export interface IMenuItemSub {
  id: TMenuItemId;
  to: string;
  label: string;
  order?: number;
  newWindow?: boolean;
  icon?: string;
  isHidden?: boolean;
  iconComponent?: (props: React.SVGAttributes<SVGElement>) => React.ReactElement;
}
