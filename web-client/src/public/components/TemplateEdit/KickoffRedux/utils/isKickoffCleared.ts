/* eslint-disable */
/* prettier-ignore */
import { IKickoff } from '../../../../types/template';
import { isArrayWithItems } from '../../../../utils/helpers';

export const isKickoffCleared = (kickoff: IKickoff) => {
  const hasFields = isArrayWithItems(kickoff.fields);

  return !hasFields && !kickoff.description;
};
