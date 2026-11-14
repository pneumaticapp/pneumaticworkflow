import { getNavMenuItem } from '../api/menu/getNavMenuItem';
import { getUserMenuItems } from '../constants/menu';
import type { IGetUserMenuItemsOptions } from '../constants/menu';
import { mapArrayIAPIMenuSubToIMenuSub } from '../redux/menu/utils/mapIAPIMenuToIMenu';
import type { IMenuItem, TMenuCounterType, TMenuCounter } from '../types/menu';
import type { TAuthUserResult } from '../types/user';

// generate the menu items sequentially: first the top-level items, and then the sub-items
export function* generateMenuItems(
  user: TAuthUserResult,
  counters?: TMenuCounter[],
  options?: IGetUserMenuItemsOptions,
): Generator<Promise<IMenuItem[]>> {
  const userMenuItems = getUserMenuItems(user, counters, options);

  yield Promise.resolve(userMenuItems);

  const itemsWithSubItems = Promise.all(
    userMenuItems.map(async (item) => {
      if (!item.subsSlug) {
        return item;
      }

      const subs = await getNavMenuItem(item.subsSlug);

      return {
        ...item,
        subs: subs?.items ? mapArrayIAPIMenuSubToIMenuSub(subs.items) : [],
      };
    }),
  );

  yield itemsWithSubItems;
}

export const createMenuCounter = (
  id: IMenuItem['id'],
  value: number | null,
  type: TMenuCounterType = 'info',
): TMenuCounter | null => {
  if (typeof value !== 'number') {
    return null;
  }

  return {
    id,
    value,
    type,
  };
};
