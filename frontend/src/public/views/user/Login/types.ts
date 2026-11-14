import type { IUserCredentials } from '../../../redux/auth/actions';
import type { EAuthUserFailType } from '../../../redux/auth/types';

export interface ILoginProps {
  loading?: boolean;
  error?: EAuthUserFailType;
  loginUser(payload: IUserCredentials): void;
  setRedirectUrl(payload: string): void;
}

export type TLoginValues = {
  email: string;
  password: string;
  rememberMe: boolean;
};
