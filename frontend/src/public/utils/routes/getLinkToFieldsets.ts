import { ERoutes } from '../../constants/routes';

export function getLinkToFieldsets(templateId: number) {
  return ERoutes.TemplateFieldsets.replace(':templateId', String(templateId));
}
