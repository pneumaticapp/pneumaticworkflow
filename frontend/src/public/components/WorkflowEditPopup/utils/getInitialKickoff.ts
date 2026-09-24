import { ITemplateKickoffClient, IRuntimeKickoffClient } from '../../../types/template';
import { ExtraFieldsHelper } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';

export function getInitialKickoff<T extends ITemplateKickoffClient | IRuntimeKickoffClient>(kickoff: T): T {
  return { ...kickoff, fields: new ExtraFieldsHelper(kickoff.fields).getFieldsWithValues() };
}
