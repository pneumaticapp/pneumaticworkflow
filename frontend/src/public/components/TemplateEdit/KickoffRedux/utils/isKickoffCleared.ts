/* eslint-disable */
/* prettier-ignore */
import { ITemplateKickoffClient } from '../../../../types/template';
import { isArrayWithItems } from '../../../../utils/helpers';

export const isKickoffCleared = (kickoff: ITemplateKickoffClient) => {
  const hasFields = isArrayWithItems(kickoff.fields);

  return !hasFields && !kickoff.description;
};
