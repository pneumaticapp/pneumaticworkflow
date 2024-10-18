/* eslint-disable */
/* prettier-ignore */
import { ERoutes } from '../../constants/routes';
import { ETemplateParts } from '../../types/template';

type TGetLinkToTemplateProps = {
  templateId: number;
  templatePart?: ETemplateParts;
};

export function getLinkToTemplate({ templateId, templatePart }: TGetLinkToTemplateProps) {
  const templateRoute = ERoutes.TemplatesEdit.replace(':id', String(templateId));
  const anchor = templatePart ? `#${templatePart}` : '';

  return  templateRoute + anchor;
}
