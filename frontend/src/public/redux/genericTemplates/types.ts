import type { IAccountGenericTemplate } from '../../types/genericTemplates';

export interface IGenericTemplatesStore {
  genericTemplates: IAccountGenericTemplate[];
  selected: number[];
  loading: boolean;
}
