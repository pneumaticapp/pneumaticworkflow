/* eslint-disable */
/* prettier-ignore */
import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { TMenuItemId } from '../../types/menu';

export interface IAPIMenuItem {
  slug: string;
  label: string;
  link?: string;
  items?: IAPIMenuItemSub[];
}

export interface IAPIMenuItemSub {
  label: string;
  link: string;
  order: number;
  slug: TMenuItemId;
}

export function getNavMenuItem(slug: string) {
  const { api: { urls }} = getBrowserConfigEnv();
  const url = urls.getNavMenuItem.replace(':slug', String(slug));

  return commonRequest<IAPIMenuItem>(url, {}, { shouldThrow: true });
}
