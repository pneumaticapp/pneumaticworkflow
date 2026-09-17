import { TForgotPassword } from '../../../redux/actions';

export interface IForgotPasswordProps {
  loading?: boolean;
  sendForgotPassword(payload: TForgotPassword): void;
}

export type TForgotPasswordValues = {
  email: string;
  captcha: string;
};

export interface ICaptchaFieldProps {
  resetSignal: number;
}
