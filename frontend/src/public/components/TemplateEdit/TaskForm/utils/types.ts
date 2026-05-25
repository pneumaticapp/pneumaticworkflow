export interface IGetLocalizedSystemVariableParams {
  apiName: string;
  title: string;
  subtitle?: string;
  formatMessage: (descriptor: { id: string }) => string;
}

export interface IGetLocalizedSystemVariableReturn {
  title: string;
  subtitle?: string;
}
