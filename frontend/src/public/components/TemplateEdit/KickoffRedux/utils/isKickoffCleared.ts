/* eslint-disable */
/* prettier-ignore */
import { IKickoffClient } from '../../../../types/template';
import { isArrayWithItems } from '../../../../utils/helpers';

export const isKickoffCleared = (kickoff: IKickoffClient) => {
  const hasFields = isArrayWithItems(kickoff.fields);

  return !hasFields && !kickoff.description;
};
