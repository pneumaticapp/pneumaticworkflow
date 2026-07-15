import { IExtraField } from '../../../types/template';

export function getTaskOutputFingerprint(output: IExtraField[]): string {
  return JSON.stringify(output);
}
