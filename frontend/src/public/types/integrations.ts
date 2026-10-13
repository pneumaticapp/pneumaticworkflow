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

export interface IApiKeyItem {
  id: number;
  name: string;
  prefix: string;
  dateCreated: string;
  lastUsedAt: string | null;
  expiresAt: string | null;
  isActive: boolean;
}

export interface IApiKeyCreateResponse extends IApiKeyItem {
  token: string;
}

export enum EIntegrations {
  Shared = 'shared',
  Zapier = 'zapier',
  API = 'api',
  Webhooks = 'webhooks',
}
