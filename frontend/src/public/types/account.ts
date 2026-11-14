export enum ESubscriptionPlan {
  Unknown = 'unknown',
  Trial = 'trial',
  Free = 'free',
  Premium = 'premium',
  Unlimited = 'unlimited',
  FractionalCOO = 'fractionalcoo',
}

export type TPlanCode = 'unlimited_month' | 'unlimited_year';

export interface IAccountPlan {
  planExpiration: string | null; // null for free plan
  maxUsers: number;
  activeUsers: number | null;
  tenantsActiveUsers: number | null;
  maxTemplates: number | null; // null for free plan
  activeTemplates: number;
  ownerName: string;
  trialEnded: boolean;
  billingPlan: ESubscriptionPlan;
  trialIsActive: boolean;
  isSubscribed: boolean;
}
