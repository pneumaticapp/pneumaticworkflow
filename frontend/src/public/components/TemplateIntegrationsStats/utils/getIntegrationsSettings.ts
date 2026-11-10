import { IntlShape } from 'react-intl';
import { EIntegrations } from '../../../types/integrations';
import { ETemplateParts } from '../../../types/template';
import { getLinkToTemplate } from '../../../utils/routes/getLinkToTemplate';

type TIntegrationSetting<T> = {
  [key in EIntegrations]: {
    title: string;
    description: string;
    anchor: string;
    link: T extends number ? string : null;
  };
};
export const getIntegrationsSettings = <T extends number | undefined>(
  templateId: T,
  formatMessage: IntlShape['formatMessage'],
): TIntegrationSetting<T> => ({
  [EIntegrations.Shared]: {
    title: formatMessage({ id: 'integrations.settings.share-title' }),
    description: formatMessage({ id: 'integrations.settings.share-description' }),
    anchor: getAnchor(ETemplateParts.Share),
    link: getLink(templateId, ETemplateParts.Share),
  },
  [EIntegrations.Zapier]: {
    title: 'Zapier',
    description: formatMessage({ id: 'integrations.settings.zapier-description' }),
    anchor: getAnchor(ETemplateParts.Zapier),
    link: getLink(templateId, ETemplateParts.Zapier),
  },
  [EIntegrations.API]: {
    title: 'API',
    description: formatMessage({ id: 'integrations.settings.api-description' }),
    anchor: getAnchor(ETemplateParts.API),
    link: getLink(templateId, ETemplateParts.API),
  },
  [EIntegrations.Webhooks]: {
    title: 'Webhooks',
    description: formatMessage({ id: 'integrations.settings.webhooks-description' }),
    anchor: getAnchor(ETemplateParts.Webhook),
    link: getLink(templateId, ETemplateParts.Webhook),
  },
});

const getAnchor = (templatePart: ETemplateParts) => {
  return `#${templatePart}`;
};

type TGetLinkReturnType<T extends number | undefined> = T extends number ? string : null;
const getLink = <T extends number | undefined>(templateId: T, templatePart: ETemplateParts): TGetLinkReturnType<T> => {
  if (typeof templateId === 'undefined') {
    return null as unknown as TGetLinkReturnType<T>;
  }

  return getLinkToTemplate({ templateId: templateId as number, templatePart }) as unknown as TGetLinkReturnType<T>;
};
