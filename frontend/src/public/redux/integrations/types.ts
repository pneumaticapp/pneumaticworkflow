import type { IApiKeyItem, IIntegrationDetailed, IIntegrationListItem } from '../../types/integrations';

export interface IIntegrationsStore {
  apiKeys: {
    isLoading: boolean;
    data: IApiKeyItem[];
    newlyCreatedKey: string | null;
  };
  list: {
    isLoading: boolean;
    data: IIntegrationListItem[];
  };
  detailed: {
    isLoading: boolean;
    data: IIntegrationDetailed | null;
  };
}
