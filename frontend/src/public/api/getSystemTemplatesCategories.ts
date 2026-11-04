import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import type { ITemplatesSystemCategories } from '../types/template';

export type TGetSystemTemplatesCategoriesResponse = ITemplatesSystemCategories[];

export function getTemplatesSystemCategories() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<TGetSystemTemplatesCategoriesResponse>(
    urls.systemTemplatesCategories,
    {},
    { shouldThrow: true },
  );
}
