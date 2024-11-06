export interface IFaqItem {
  order: number;
  question: string;
  answer: string;
}

export interface IBillingDetails {
  address: string;
  addressExtra?: string;
  city: string;
  discount: number;
  country: string;
  email: string;
  firstName: string;
  lastName: string;
  region: string;
  zipCode: string;
}

export interface IReccurlyValidationError {
  code: string;
  message: string;
  fields: string[];
  details: object[];
}

export interface IReccurlySubmitError {
  name: string;
  code: string;
  message: string;
  fields: string[];
}

export interface IReccurlyToken {
  type: string;
  id: string;
  error: IReccurlyValidationError;
}

export interface IPayTypeOption {
  key: number;
  value: EPayPeriod;
  label: string;
}

export enum EPayPeriod {
  Monthly = 'unlimited_month',
  Annually = 'unlimited_year',
}

export enum EBillingPeriod {
  Monthly = 'month',
  Annually = 'year',
}
