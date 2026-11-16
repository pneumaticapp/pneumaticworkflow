import 'axios';

declare module 'axios' {
  export interface AxiosRequestConfig {
    expectedErrorStatuses?: number[];
  }
}
