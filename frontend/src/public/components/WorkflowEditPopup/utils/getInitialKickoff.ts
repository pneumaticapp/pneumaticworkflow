/* eslint-disable */
/* prettier-ignore */
import { IKickoff } from '../../../types/template';
import { ExtraFieldsHelper } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';

export function getInitialKickoff(kickoff: IKickoff): IKickoff {
  return { ...kickoff, fields: new ExtraFieldsHelper(kickoff.fields).getFieldsWithValues() };
}
