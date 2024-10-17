export interface IAuthenticatedUser {
  id: string;
  email: string;
  account: IAuthenticatedAccount;
  first_name: string;
  last_name: string;
  phone: string;
  photo: string;
  is_staff: boolean;
  date_joined: string;
  is_account_owner: boolean;
  is_admin: boolean;
}

export interface IAuthenticatedAccount {
  id: number;
  name: string;
  date_joined: string;
  is_blocked: boolean;
  is_subscribed: boolean;
  is_verified: boolean;
  owner_email: string;
  payment_card_provided: boolean;
}
