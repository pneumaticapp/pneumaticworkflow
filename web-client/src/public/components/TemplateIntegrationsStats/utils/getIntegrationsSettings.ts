import { EIntegrations } from '../../../types/integrations';
import { ETemplateParts } from '../../../types/template';
import { getLinkToTemplate } from '../../../utils/routes/getLinkToTemplate';

type TIntegrationSetting<T> = {
  [key in EIntegrations] : {
    title: string;
    description: string;
    anchor: string;
    link: T extends number ? string : null;
  }
}
export const getIntegrationsSettings = <T extends number | undefined>(templateId: T): TIntegrationSetting<T>  => ({
  [EIntegrations.Shared]: {
    title: 'Share Kick-off',
    description: 'Create a link to enable users to launch workflows from outside Pneumatic',
    anchor: getAnchor(ETemplateParts.Share),
    link: getLink(templateId, ETemplateParts.Share),
  },
  [EIntegrations.Zapier]: {
    title: 'Zapier',
    description: 'Build tirgger-action type integrations with thousands of apps supported by zapier',
    anchor: getAnchor(ETemplateParts.Zapier),
    link: getLink(templateId, ETemplateParts.Zapier),
  },
  [EIntegrations.API]: {
    title: 'API',
    description: 'Develop highly customized integrations with any software whatsoever',
    anchor: getAnchor(ETemplateParts.API),
    link: getLink(templateId, ETemplateParts.API),
  },
  [EIntegrations.Webhooks]: {
    title: 'Webhooks',
    description: 'Get notifications in real time when specific events happen in Pneumatic',
    anchor: getAnchor(ETemplateParts.Webhook),
    link: getLink(templateId, ETemplateParts.Webhook),
  },
});


const getAnchor = (templatePart: ETemplateParts) => {
  return `#${templatePart}`;
}

type TGetLinkReturnType<T extends number | undefined> = T extends number ? string : null;
const getLink = <T extends number | undefined>(templateId: T, templatePart: ETemplateParts): TGetLinkReturnType<T> => {
  if (typeof templateId === 'undefined') {
    return null as unknown as TGetLinkReturnType<T>;
  }

  return getLinkToTemplate({ templateId: templateId as number, templatePart }) as unknown as TGetLinkReturnType<T>;
}
