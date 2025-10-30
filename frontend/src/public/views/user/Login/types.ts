import { EAuthUserFailType, IUserCredentials } from "../../../redux/actions";

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