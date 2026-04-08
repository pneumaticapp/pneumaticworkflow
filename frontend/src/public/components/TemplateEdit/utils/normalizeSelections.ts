import { IExtraFieldSelection } from '../../../types/template';

export function normalizeSelections(selections?: IExtraFieldSelection[] | string[]): string[] {
  if (!selections?.length) return [];
  if (typeof selections[0] === 'string') return selections as string[];
  return (selections as IExtraFieldSelection[]).map((item) => item.value);
}
