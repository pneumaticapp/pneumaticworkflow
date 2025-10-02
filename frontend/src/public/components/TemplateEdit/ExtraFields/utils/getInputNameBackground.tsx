/* eslint-disable */
/* prettier-ignore */
import { EInputNameBackgroundColor } from '../../../../types/workflow';

import styles from '../../KickoffRedux/KickoffRedux.css';

/*
  These ones applies depends on mode in order to fix safari/chrome bugs with transparency
  and default user agents, if there's new modes with custom colors, you have to apply a new one here
  and in KickoffRedux styles
*/

export const getInputNameBackground = (labelBackgroundColor?: EInputNameBackgroundColor) => {

  if (!labelBackgroundColor) {
    return undefined;
  }

  const fieldsMap: { [key in EInputNameBackgroundColor]: string } = {
    [EInputNameBackgroundColor.White]: styles['kick-off-input__name_kickoff'],
    [EInputNameBackgroundColor.OrchidWhite]: styles['kick-off-input__name_process-run'],
  };

  return fieldsMap[labelBackgroundColor];
};
