/* eslint-disable */
/* prettier-ignore */
import { IKickoffClient } from '../../../types/template';
import { ExtraFieldsHelper } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';

export function getInitialKickoff(kickoff: IKickoffClient): IKickoffClient {
  return { ...kickoff, fields: new ExtraFieldsHelper(kickoff.fields).getFieldsWithValues() };
}
