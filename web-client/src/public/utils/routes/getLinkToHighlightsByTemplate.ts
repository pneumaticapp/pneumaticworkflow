/* eslint-disable */
/* prettier-ignore */
import { ERoutes } from '../../constants/routes';

export function getLinkToHighlightsByTemplate(templateId: number) {
  return ERoutes.HighlightsByTemplateId.replace(':templateId', String(templateId));
}
