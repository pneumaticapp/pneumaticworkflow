export interface IIntegrationListItem {
  id: number;
  name: string;
  logo: string;
  shortDescription: string;
}

export interface IIntegrationDetailed {
  id: number;
  name: string;
  logo: string;
  longDescription: string;
  buttonText: string;
  url: string;
}

export enum EIntegrations {
  Shared = 'shared',
  Zapier = 'zapier',
  API = 'api',
  Webhooks = 'webhooks',
}
