import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplatesSystemCategories } from '../types/redux';

export type TGetSystemTemplatesCategoriesResponse = ITemplatesSystemCategories[];

export function getTemplatesSystemCategories() {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest<TGetSystemTemplatesCategoriesResponse>(
    urls.systemTemplatesCategories,
    {}, {shouldThrow: true},
  );
}
