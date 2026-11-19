import type { ITemplateClient, TAITemplateGenerationStatus } from '../../types/template';

export enum ETemplateStatus {
  Loading = 'loading',
  LoadingFailed = 'loading-failed',
  Saved = 'saved',
  Saving = 'saving',
  SaveFailed = 'save-failed',
  Sharing = 'Sharing',
  SaveCanceled = 'save-canceled',
}

export interface ITemplateStore {
  data: ITemplateClient;
  status: ETemplateStatus;
  AITemplate: {
    isModalOpened: boolean;
    generationStatus: TAITemplateGenerationStatus;
    generatedData: ITemplateClient | null;
  };
}
