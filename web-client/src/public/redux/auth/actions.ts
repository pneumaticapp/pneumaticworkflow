import { IUnsavedUser, TUserInvited } from '../../types/user';
import { actionGenerator } from '../../utils/redux';
import { IAuthUser, ITypedReduxAction } from '../../types/redux';
import { IUpdateUserRequest, TUpdateUserMappedResponse } from '../../api/editProfile';
import { IUpdateAccountRequest, IUpdatedAccount } from '../../api/editAccount';
import { TPlanCode } from '../../types/account';

export const enum EAuthActions {
  AuthUser = 'AUTH_USER',
  ChangePassword = 'CHANGE_PASSWORD',
  ChangePasswordFail = 'CHANGE_PASSWORD_FAIL',
  ChangePasswordSuccess = 'CHANGE_PASSWORD_SUCCESS',
  EditAccount = 'EDIT_ACCOUNT',
  EditAccountSuccess = 'EDIT_ACCOUNT_SUCCESS',
  EditUser = 'EDIT_USER',
  EditUserSuccess = 'EDIT_USER_SUCCESS',
  EditFailed = 'EDIT_FAILED',
  ForgotPassword = 'FORGOT_PASSWORD',
  ForgotPasswordSuccess = 'FORGOT_PASSWORD_SUCCESS',
  ForgotPasswordFail = 'FORGOT_PASSWORD_FAIL',
  ResetPassword = 'RESET_PASSWORD',
  ResetPasswordSuccess = 'RESET_PASSWORD_SUCCESS',
  ResetPasswordFail = 'RESET_PASSWORD_FAIL',
  AuthUserSuccess = 'AUTH_USER_SUCCESS',
  AuthUserFail = 'AUTH_USER_FAIL',
  LoginUser = 'LOGIN_USER',
  LoginSuperuser = 'LOGIN_SUPERUSER',
  LoginPartnerSuperuser = 'LOGIN_PARTNER_SUPERUSER',
  ReturnFromSupermode = 'RETURN_FROM_SUPERMODE',
  RegisterUser = 'REGISTER_USER',
  RegisterUserInvited = 'REGISTER_USER_INVITED',
  RegisterUserSuccess = 'REGISTER_USER_SUCCESS',
  LogoutUser = 'LOGOUT_USER',
  LogoutUserSuccess = 'LOGOUT_USER_SUCCESS',
  RemoveGoogleUser = 'REMOVE_GOOGLE_USER',
  ResendVerification = 'RESEND_VERIFICATION',
  RedirectToLogin = 'REDIRECT_TO_LOGIN',
  SetRedirectUrl = 'SET_REDIRECT_URL',
  SetToken = 'SET_USER_TOKEN',
  WatchUserWSEvents = 'WATCH_USER_WS_EVENTS',
  UploadUserPhoto = 'UPLOAD_USER_PHOTO',
  DeleteUserPhoto = 'DELETE_USER_PHOTP',
  SetUserPhoto = 'SET_USER_PHOTO',
  CollectPaymentDetails = 'COLLECT_PAYMENT_DETAILS',
  ChangePaymentDetails = 'CHANGE_PAYMENT_DETAILS',
  MakeStripePayment = 'MAKE_STRIPE_PAYMENT',
  OnAfterPaymentDetailsProvided = 'AFTER_PAYMENT_DEATILS_PROVIDED',
  RedirectToCustomerPortal = 'REDIRECT_TO_CUSTOMER_PORTAL',
}

export interface IUserCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export type TForgotPassword = Pick<IUserCredentials, 'email'>;
export type TChangePassword = IConfirmChangePassword;

export interface IUserRegister {
  email: string;
  firstName: string;
  lastName: string;
  photo: string;
  fromEmail: boolean;
  timezone: string;
  password?: string;
  phone?: string;
  companyName?: string;
}

export interface IConfirmResetPassword {
  newPassword: string;
  confirmNewPassword: string;
  token: string;
}

export interface IConfirmChangePassword {
  oldPassword: string;
  newPassword: string;
  confirmNewPassword: string;
}

export type TAuthUserResult = Omit<IAuthUser, 'loading' | 'error' | 'superUserToken' | 'loggedState'>;

export type TAuthSuccessResult = Pick<IUnsavedUser, 'token'>;

export type TAuthUser = ITypedReduxAction<EAuthActions.AuthUser, void>;
export const authenticateUser: (payload?: void) => TAuthUser = actionGenerator<EAuthActions.AuthUser, void>(
  EAuthActions.AuthUser,
);

export type TEditUser = ITypedReduxAction<EAuthActions.EditUser, IUpdateUserRequest>;
export const editCurrentUser: (payload: IUpdateUserRequest) => TEditUser = actionGenerator<
  EAuthActions.EditUser,
  IUpdateUserRequest
>(EAuthActions.EditUser);

export type TEditAccount = ITypedReduxAction<EAuthActions.EditAccount, IUpdateAccountRequest>;
export const editCurrentAccount: (payload: IUpdateAccountRequest) => TEditAccount = actionGenerator<
  EAuthActions.EditAccount,
  IUpdateAccountRequest
>(EAuthActions.EditAccount);

export type TSendForgotPassword = ITypedReduxAction<EAuthActions.ForgotPassword, TForgotPassword>;
export const sendForgotPassword: (payload: TForgotPassword) => TSendForgotPassword = actionGenerator<
  EAuthActions.ForgotPassword,
  TForgotPassword
>(EAuthActions.ForgotPassword);

export type TSendForgotPasswordSuccess = ITypedReduxAction<EAuthActions.ForgotPasswordSuccess, void>;
export const sendForgotPasswordSuccess: (payload?: void) => TSendForgotPasswordSuccess = actionGenerator<
  EAuthActions.ForgotPasswordSuccess,
  void
>(EAuthActions.ForgotPasswordSuccess);

export type TSendForgotPasswordFail = ITypedReduxAction<EAuthActions.ForgotPasswordFail, void>;
export const sendForgotPasswordFail: (payload?: void) => TSendForgotPasswordFail = actionGenerator<
  EAuthActions.ForgotPasswordFail,
  void
>(EAuthActions.ForgotPasswordFail);

export type TSendResetPassword = ITypedReduxAction<EAuthActions.ResetPassword, IConfirmResetPassword>;
export const sendResetPassword: (payload: IConfirmResetPassword) => TSendResetPassword = actionGenerator<
  EAuthActions.ResetPassword,
  IConfirmResetPassword
>(EAuthActions.ResetPassword);

export type TSendResetPasswordSuccess = ITypedReduxAction<EAuthActions.ResetPasswordSuccess, TAuthSuccessResult>;
export const sendResetPasswordSuccess: (payload: TAuthSuccessResult) => TSendResetPasswordSuccess = actionGenerator<
  EAuthActions.ResetPasswordSuccess,
  TAuthSuccessResult
>(EAuthActions.ResetPasswordSuccess);

export type TSendResetPasswordFail = ITypedReduxAction<EAuthActions.ResetPasswordFail, void>;
export const sendResetPasswordFail: (payload?: void) => TSendResetPasswordFail = actionGenerator<
  EAuthActions.ResetPasswordFail,
  void
>(EAuthActions.ResetPasswordFail);

export type TSendChangePassword = ITypedReduxAction<EAuthActions.ChangePassword, IConfirmChangePassword>;
export const sendChangePassword: (payload: IConfirmChangePassword) => TSendChangePassword = actionGenerator<
  EAuthActions.ChangePassword,
  IConfirmChangePassword
>(EAuthActions.ChangePassword);

export type TSendChangePasswordSuccess = ITypedReduxAction<EAuthActions.ChangePasswordSuccess, void>;
export const sendChangePasswordSuccess: (payload?: void) => TSendChangePasswordSuccess = actionGenerator<
  EAuthActions.ChangePasswordSuccess,
  void
>(EAuthActions.ChangePasswordSuccess);

export type TSendChangePasswordFail = ITypedReduxAction<EAuthActions.ChangePasswordFail, void>;
export const sendChangePasswordFail: (payload?: void) => TSendChangePasswordFail = actionGenerator<
  EAuthActions.ChangePasswordFail,
  void
>(EAuthActions.ChangePasswordFail);

export type TEditUserSuccess = ITypedReduxAction<EAuthActions.EditUserSuccess, TUpdateUserMappedResponse>;
export const editCurrentUserSuccess: (payload: TUpdateUserMappedResponse) => TEditUserSuccess = actionGenerator<
  EAuthActions.EditUserSuccess,
  TUpdateUserMappedResponse
>(EAuthActions.EditUserSuccess);

export type TEditAccountSuccess = ITypedReduxAction<EAuthActions.EditAccountSuccess, IUpdatedAccount>;
export const editCurrentAccountSuccess: (payload: IUpdatedAccount) => TEditAccountSuccess = actionGenerator<
  EAuthActions.EditAccountSuccess,
  IUpdatedAccount
>(EAuthActions.EditAccountSuccess);

export type TAuthUserSuccess = ITypedReduxAction<EAuthActions.AuthUserSuccess, TAuthUserResult>;
export const authUserSuccess: (payload: TAuthUserResult) => TAuthUserSuccess = actionGenerator<
  EAuthActions.AuthUserSuccess,
  TAuthUserResult
>(EAuthActions.AuthUserSuccess);

export enum EAuthUserFailType {
  Common = 'common',
  NotVerified = 'not-verified',
}

export type TAuthUserFail = ITypedReduxAction<EAuthActions.AuthUserFail, EAuthUserFailType>;
export const authUserFail: (payload?: EAuthUserFailType) => TAuthUserFail = actionGenerator<
  EAuthActions.AuthUserFail,
  EAuthUserFailType
>(EAuthActions.AuthUserFail);

export type TEditAccountFail = ITypedReduxAction<EAuthActions.EditFailed, void>;
export const accountEditFailed: (payload: void) => TEditAccountFail = actionGenerator<EAuthActions.EditFailed, void>(
  EAuthActions.EditFailed,
);

export type TEditProfileFail = ITypedReduxAction<EAuthActions.EditFailed, void>;
export const profileEditFailed: (payload: void) => TEditAccountFail = actionGenerator<EAuthActions.EditFailed, void>(
  EAuthActions.EditFailed,
);

export type TLoginUser = ITypedReduxAction<EAuthActions.LoginUser, IUserCredentials>;
export const loginUser: (payload: IUserCredentials) => TLoginUser = actionGenerator<
  EAuthActions.LoginUser,
  IUserCredentials
>(EAuthActions.LoginUser);

export type TLoginSuperuserPayload = { email: string };
export type TLoginSuperuser = ITypedReduxAction<EAuthActions.LoginSuperuser, TLoginSuperuserPayload>;
export const loginSuperuser: (payload: TLoginSuperuserPayload) => TLoginSuperuser = actionGenerator<
  EAuthActions.LoginSuperuser,
  TLoginSuperuserPayload
>(EAuthActions.LoginSuperuser);

export type TLoginPartnerSuperuserPayload = { tenantId: number };
export type TLoginPartnerSuperuser = ITypedReduxAction<
  EAuthActions.LoginPartnerSuperuser,
  TLoginPartnerSuperuserPayload
>;
export const loginPartnerSuperuser: (payload: TLoginPartnerSuperuserPayload) => TLoginPartnerSuperuser =
  actionGenerator<EAuthActions.LoginPartnerSuperuser, TLoginPartnerSuperuserPayload>(
    EAuthActions.LoginPartnerSuperuser,
  );

export type TReturnFromSupermode = ITypedReduxAction<EAuthActions.ReturnFromSupermode, void>;
export const returnFromSupermode: () => TReturnFromSupermode = actionGenerator(EAuthActions.ReturnFromSupermode);

export type TRegisterUserPayload = {
  user: IUserRegister;
  captcha?: string;
  onStart?(): void;
  onFinish?(): void;
};
export type TRegisterUser = ITypedReduxAction<EAuthActions.RegisterUser, TRegisterUserPayload>;
export const registerUser: (payload: TRegisterUserPayload) => TRegisterUser = actionGenerator<
  EAuthActions.RegisterUser,
  TRegisterUserPayload
>(EAuthActions.RegisterUser);

export type TRegisterUserSuccess = ITypedReduxAction<EAuthActions.RegisterUserSuccess, IUnsavedUser>;
export const registerUserSuccess: (payload: IUnsavedUser) => TRegisterUserSuccess = actionGenerator<
  EAuthActions.RegisterUserSuccess,
  IUnsavedUser
>(EAuthActions.RegisterUserSuccess);

export type TLogoutUserPayload =
  | {
      showLoader?: boolean;
      redirectUrl?: string | null;
    }
  | undefined;

export type TLogoutUser = ITypedReduxAction<EAuthActions.LogoutUser, TLogoutUserPayload>;
export const logoutUser: (payload?: TLogoutUserPayload) => TLogoutUser = actionGenerator<
  EAuthActions.LogoutUser,
  TLogoutUserPayload
>(EAuthActions.LogoutUser);

export type TLogoutUserSuccess = ITypedReduxAction<EAuthActions.LogoutUserSuccess, void>;
export const logoutUserSuccess: (payload?: void) => TLogoutUserSuccess = actionGenerator<
  EAuthActions.LogoutUserSuccess,
  void
>(EAuthActions.LogoutUserSuccess);

export type TRemoveGoogleUser = ITypedReduxAction<EAuthActions.RemoveGoogleUser, void>;
export const removeGoogleUser: (payload?: void) => TRemoveGoogleUser = actionGenerator<
  EAuthActions.RemoveGoogleUser,
  void
>(EAuthActions.RemoveGoogleUser);

export type TRegisterUserInvited = ITypedReduxAction<EAuthActions.RegisterUserInvited, TUserInvited>;
export const registerUserInvited: (payload: TUserInvited) => TRegisterUserInvited = actionGenerator<
  EAuthActions.RegisterUserInvited,
  TUserInvited
>(EAuthActions.RegisterUserInvited);

export type TResendVerification = ITypedReduxAction<EAuthActions.ResendVerification, void>;
export const resendVerification: (payload?: void) => TResendVerification = actionGenerator<
  EAuthActions.ResendVerification,
  void
>(EAuthActions.ResendVerification);

export type TRedirectToLogin = ITypedReduxAction<EAuthActions.RedirectToLogin, void>;
export const redirectToLogin: (payload?: void) => TRedirectToLogin = actionGenerator<
  EAuthActions.RedirectToLogin,
  void
>(EAuthActions.RedirectToLogin);

export type TSetRedirectUrl = ITypedReduxAction<EAuthActions.SetRedirectUrl, string>;
export const setRedirectUrl: (payload: string) => TSetRedirectUrl = actionGenerator<
  EAuthActions.SetRedirectUrl,
  string
>(EAuthActions.SetRedirectUrl);

export type TSetUserToken = ITypedReduxAction<EAuthActions.SetToken, string>;
export const setUserToken: (payload: string) => TSetUserToken = actionGenerator<EAuthActions.SetToken, string>(
  EAuthActions.SetToken,
);

export type TWatchUserWSEvents = ITypedReduxAction<EAuthActions.WatchUserWSEvents, void>;
export const watchUserWSEventsAction: (payload?: void) => TWatchUserWSEvents = actionGenerator<
  EAuthActions.WatchUserWSEvents,
  void
>(EAuthActions.WatchUserWSEvents);

type TUploadUserPhotoPayload = {
  photo: Blob;
  onComplete?(): void;
};
export type TUploadUserPhoto = ITypedReduxAction<EAuthActions.UploadUserPhoto, TUploadUserPhotoPayload>;
export const uploadUserPhoto: (payload: TUploadUserPhotoPayload) => TUploadUserPhoto = actionGenerator<
  EAuthActions.UploadUserPhoto,
  TUploadUserPhotoPayload
>(EAuthActions.UploadUserPhoto);

export type TDeleteUserPhoto = ITypedReduxAction<EAuthActions.DeleteUserPhoto, void>;
export const deleteUserPhoto: (payload?: void) => TDeleteUserPhoto = actionGenerator<
  EAuthActions.DeleteUserPhoto,
  void
>(EAuthActions.DeleteUserPhoto);

export type TSetUserPhoto = ITypedReduxAction<EAuthActions.SetUserPhoto, IAuthUser['photo']>;
export const setUserPhoto: (payload: IAuthUser['photo']) => TSetUserPhoto = actionGenerator<
  EAuthActions.SetUserPhoto,
  IAuthUser['photo']
>(EAuthActions.SetUserPhoto);

export type TMakeStripePaymentPayload = {
  successUrl: string;
  cancelUrl: string;
  code: TPlanCode;
  quantity?: number;
  showLoader?: boolean;
};
export type TMakeStripePayment = ITypedReduxAction<EAuthActions.MakeStripePayment, TMakeStripePaymentPayload>;
export const makeStripePayment: (payload: TMakeStripePaymentPayload) => TMakeStripePayment = actionGenerator<
  EAuthActions.MakeStripePayment,
  TMakeStripePaymentPayload
>(EAuthActions.MakeStripePayment);

export type TCollectPaymentDetails = ITypedReduxAction<EAuthActions.CollectPaymentDetails, void>;
export const collectPaymentDetails: (payload?: void) => TCollectPaymentDetails = actionGenerator<
  EAuthActions.CollectPaymentDetails,
  void
>(EAuthActions.CollectPaymentDetails);

export type TChangePaymentDetails = ITypedReduxAction<EAuthActions.ChangePaymentDetails, void>;
export const changePaymentDetails: (payload?: void) => TChangePaymentDetails = actionGenerator<
  EAuthActions.ChangePaymentDetails,
  void
>(EAuthActions.ChangePaymentDetails);

export type TOnAfterPaymentDetailsProvided = ITypedReduxAction<EAuthActions.OnAfterPaymentDetailsProvided, void>;
export const onAfterPaymentDetailsProvided: (payload?: void) => TOnAfterPaymentDetailsProvided = actionGenerator<
  EAuthActions.OnAfterPaymentDetailsProvided,
  void
>(EAuthActions.OnAfterPaymentDetailsProvided);

export type TRedirectToCustomerPortal = ITypedReduxAction<EAuthActions.RedirectToCustomerPortal, void>;
export const redirectToCustomerPortal: (payload?: void) => TRedirectToCustomerPortal = actionGenerator<
  EAuthActions.RedirectToCustomerPortal,
  void
>(EAuthActions.RedirectToCustomerPortal);

export type TAuthActions =
  | TRegisterUser
  | TAuthUser
  | TAuthUserSuccess
  | TLoginUser
  | TLoginSuperuser
  | TRegisterUser
  | TRegisterUserSuccess
  | TLogoutUser
  | TLogoutUserSuccess
  | TAuthUserFail
  | TRemoveGoogleUser
  | TRegisterUserInvited
  | TEditAccount
  | TEditUser
  | TEditUserSuccess
  | TEditAccountSuccess
  | TSendChangePassword
  | TSendChangePasswordFail
  | TSendChangePasswordSuccess
  | TSendForgotPassword
  | TSendForgotPasswordSuccess
  | TSendForgotPasswordFail
  | TSendResetPassword
  | TSendResetPasswordSuccess
  | TSendResetPasswordFail
  | TEditAccountFail
  | TEditProfileFail
  | TResendVerification
  | TRedirectToLogin
  | TSetRedirectUrl
  | TSetUserToken
  | TWatchUserWSEvents
  | TUploadUserPhoto
  | TDeleteUserPhoto
  | TSetUserPhoto
  | TLoginPartnerSuperuser
  | TReturnFromSupermode
  | TCollectPaymentDetails
  | TChangePaymentDetails
  | TMakeStripePayment
  | TOnAfterPaymentDetailsProvided
  | TRedirectToCustomerPortal;
