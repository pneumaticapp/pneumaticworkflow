import { all, call, fork, put, takeEvery, takeLatest, select, takeLeading } from 'redux-saga/effects';
import { auth } from '../../api/auth';
import {
  accountEditFailed,
  authUserFail,
  authUserSuccess,
  EAuthActions,
  editCurrentAccountSuccess,
  editCurrentUserSuccess,
  IConfirmResetPassword,
  profileEditFailed,
  registerUserSuccess,
  sendForgotPasswordFail,
  sendForgotPasswordSuccess,
  sendResetPasswordFail,
  sendResetPasswordSuccess,
  TAuthUserResult,
  TEditAccount,
  TEditUser,
  TLoginUser,
  TRegisterUser,
  TRegisterUserInvited,
  TSendChangePassword,
  TSendForgotPassword,
  TSendResetPassword,
  sendChangePasswordSuccess,
  sendChangePasswordFail,
  EAuthUserFailType,
  redirectToLogin,
  TSetRedirectUrl,
  TSetUserToken,
  setUserToken,
  TLoginSuperuser,
  IUserRegister,
  TUploadUserPhoto,
  setUserPhoto,
  logoutUserSuccess,
  TLoginPartnerSuperuser,
  TLogoutUser,
  TMakeStripePayment,
  makeStripePayment,
} from './actions';

import { resendVerification } from '../../api/resendVerification';
import { ERoutes } from '../../constants/routes';
import { NotificationManager } from '../../components/UI/Notifications';
import { setJwtCookie, removeAuthCookies } from '../../utils/authCookie';
import { setOAuthRegistrationCompleted } from '../../api/setOAuthRegistrationCompleted';
import { TUserInvited } from '../../types/user';
import { getAuthUser, getInvitedUser } from '../selectors/user';
import { getOAuthId, getOAuthType } from '../../utils/auth';
import { editProfile, IUpdateUserRequest, IUpdateUserResponse, TUpdateUserMappedResponse } from '../../api/editProfile';
import { logger } from '../../utils/logger';
import { mapToCamelCase } from '../../utils/mappers';
import { resetPassword } from '../../api/resetPassword';
import { ICustomError, getErrorMessage } from '../../utils/getErrorMessage';
import { IResetPasswordSetResponse, resetPasswordSet } from '../../api/resetPasswordSet';
import { editAccount, IUpdateAccountResponse } from '../../api/editAccount';
import { changePassword, IChangePasswordResponse } from '../../api/changePassword';
import { analytics } from '../../utils/analytics';
import { sendSignOut } from '../../api/sendSignOut';
import { REDIRECT_URL_STORAGE_KEY } from '../../constants/storageKeys';
import { getUTMParams, IUserUtm } from '../../views/user/utils/utmParams';
import { clearAppFilters, setGeneralLoaderVisibility } from '../general/actions';
import { getQueryStringParams, history } from '../../utils/history';
import { watchNewTask, watchRemoveTask } from '../tasks/saga';
import { watchNewNotifications } from '../notifications/saga';
import { TUploadedFile, uploadUserAvatar } from '../../utils/uploadFiles';
import { changePhotoProfile } from '../../api/changePhotoProfile';
import { ELoggedState, IAuthUser } from '../../types/redux';
import { resetFirebaseDeviceToken } from '../../firebase';
import { getTenantToken, IGetTenantTokenResponse } from '../../api/tenants/getTenantToken';
import { resetSuperuserToken, setSuperuserToken } from './utils/superuserToken';
import {
  getSuperuserReturnRoute,
  resetSuperuserReturnRoute,
  setSuperuserReturnRoute,
} from './utils/superuserReturnRoute';
import { IMakePaymentResponse, makePayment } from '../../api/makePayment';
import { fetchPlan } from '../accounts/saga';
import { getAbsolutePath } from '../../utils/getAbsolutePath';
import { ICardSetupResponse, cardSetup } from '../../api/cardSetup';
import { confirmPaymentDetailsProvided } from './utils/confirmPaymentDetailsProvided';
import { createAITemplate } from './utils/createAITemplate';
import { trackCrozdesk } from '../../utils/analytics/trackCrozdesk';
import { getBrowserConfig } from '../../utils/getConfig';
import { getCustomerPortalLink } from '../../api/getCustomerPortalLink';
import { createTemplateFromName } from './utils/createTemplateFromName';
import { ITemplate } from '../../types/template';
import { watchNewWorkflowsEvent } from '../workflows/saga';
import { removeLocalStorage } from '../../utils/localStorage';

import { isEnvBilling } from '../../constants/enviroment';

export function* authenticateUser(redirectUrl?: string) {
  try {
    const user: TAuthUserResult = yield call(auth.getUser);
    yield put(authUserSuccess(user));

    if (isEnvBilling && !user.account.paymentCardProvided) {
      if (user.account.isSubscribed) {
        yield call(changePaymentDetailsSaga);
        return;
      }

      history.push(ERoutes.CollectPaymentDetails);
      return;
    }

    if (redirectUrl) {
      history.replace(redirectUrl);
    }
  } catch (err) {
    logger.error(err);
    yield put(redirectToLogin());
    yield put(authUserFail());
  }
}

export function* authUserSaga() {
  yield authenticateUser();
}

export const loginWithEmailPasswordAsync = (email: string, password: string) =>
  auth
    .signInWithEmailAndPassword(email, password)
    .then((authUser) => authUser)
    .catch((error) => error);

export function* loginWithEmailPassword({ payload }: TLoginUser) {
  const { email, password, rememberMe } = payload;
  try {
    const loginUser: ICustomError & IAuthUser = yield call(loginWithEmailPasswordAsync, email, password);
    if (!loginUser.message) {
      setJwtCookie(loginUser.token, rememberMe);
      yield authenticateUser(loginUser.isAccountOwner ? ERoutes.Main : ERoutes.Tasks);
      return;
    }

    const err = getErrorMessage(loginUser);
    const isVerificationError = err.includes('Your account has not been verified');

    if (isVerificationError) {
      NotificationManager.error({ title: 'Login failed', message: err });
      yield put(authUserFail(EAuthUserFailType.NotVerified));
    } else {
      yield put(authUserFail(EAuthUserFailType.Common));
    }
  } catch (error) {
    yield put(authUserFail(EAuthUserFailType.Common));
  }
}

export function* loginSuperuser({ payload }: TLoginSuperuser) {
  const { email } = payload;

  try {
    const loginUser: TAuthUserResult = yield call(auth.signInAsSuperuser, email);
    setSuperuserToken(loginUser.token);
    yield authenticateUser(ERoutes.Main);
  } catch (error) {
    NotificationManager.error({
      title: 'Login failed',
      message: getErrorMessage(error),
    });
    yield put(authUserFail(EAuthUserFailType.Common));
  }
}

export function* loginPartnerSuperuser({ payload: { tenantId } }: TLoginPartnerSuperuser) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const result: IGetTenantTokenResponse = yield call(getTenantToken, tenantId);
    yield handleLogoutUnsubscribing({ shouldExpireToken: false });

    setSuperuserToken(result.token);
    setSuperuserReturnRoute(history.location.pathname);
    yield authenticateUser(ERoutes.Main);
  } catch (error) {
    NotificationManager.error({
      title: 'Login failed',
      message: getErrorMessage(error),
    });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* retrunFromSupermodeSaga() {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield handleLogoutUnsubscribing({ shouldExpireToken: false });
    const returnRoute = getSuperuserReturnRoute() || ERoutes.Main;
    yield authenticateUser(returnRoute);
    resetSuperuserReturnRoute();
  } catch (error) {
    NotificationManager.error({
      title: 'Login failed',
      message: getErrorMessage(error),
    });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export const registerWithEmailAsync = (user: IUserRegister, utmParams?: IUserUtm, captcha?: string) =>
  auth
    .createUserWithEmail(user, utmParams, captcha)
    .then((authUser) => authUser)
    .catch((error) => error);

export function* registerWithEmailPassword({ payload: { user, captcha, onStart, onFinish } }: TRegisterUser) {
  try {
    onStart?.();
    const utmParams = getUTMParams();
    const registerUser: ICustomError & IAuthUser = yield call(registerWithEmailAsync, user, utmParams, captcha);

    if (!registerUser.message && registerUser.token) {
      yield put(registerUserSuccess(registerUser));

      setJwtCookie(registerUser.token);

      const [id, type] = [getOAuthId(), getOAuthType()];
      if (id && type) {
        setOAuthRegistrationCompleted(id, type).catch((error) => error);
      }

      yield authenticateUser(ERoutes.Templates);
    } else {
      console.info('register failed :', registerUser.message);
      NotificationManager.error({
        title: 'Register failed',
        message: registerUser.message,
      });
      yield put(authUserFail());
    }
  } catch (error) {
    console.info('register error : ', String(error));
    yield put(authUserFail());
  } finally {
    onFinish?.();
  }
}

export const registerInviteAsync = (id: string, body: TUserInvited) =>
  auth
    .createUserWithInvite(id, body)
    .then((authUser) => authUser)
    .catch((error) => error);

export function* registerWithInvite({ payload }: TRegisterUserInvited) {
  const {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    invitedUser: { id },
  }: ReturnType<typeof getInvitedUser> = yield select(getInvitedUser);
  if (!id) {
    yield put(authUserFail());

    return;
  }
  try {
    const user: ICustomError & IAuthUser = yield call(registerInviteAsync, id, payload);
    if (!user.message && user.token) {
      yield put(registerUserSuccess(user));

      setJwtCookie(user.token);

      yield call(authenticateUser, ERoutes.Main);
    } else {
      console.info('register failed :', user.message);
      NotificationManager.error({
        title: 'Register failed',
        message: user.message,
      });
      yield put(authUserFail());
    }
  } catch (error) {
    console.info('register error : ', String(error));
    yield put(authUserFail());
  }
}

function* handleLogoutUnsubscribing({ shouldExpireToken }: { shouldExpireToken: boolean }) {
  yield put(clearAppFilters());
  resetFirebaseDeviceToken();
  resetSuperuserToken();
  analytics.reset();

  if (shouldExpireToken) {
    yield sendSignOut();
    removeAuthCookies();
    removeLocalStorage();
  }
}

export function* logout(action: TLogoutUser) {
  const { showLoader, redirectUrl } = {
    showLoader: true,
    redirectUrl: ERoutes.Login,
    ...action.payload,
  };
  try {
    const { authUser }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);
    if (authUser.loggedState === ELoggedState.LoggedOut) {
      return;
    }

    if (showLoader) {
      yield put(setGeneralLoaderVisibility(true));
    }

    yield handleLogoutUnsubscribing({ shouldExpireToken: true });

    yield put(logoutUserSuccess());

    if (redirectUrl) {
      yield put(redirectToLogin());
    }
  } catch (error) {
    logger.error('logout error:', error);
  } finally {
    if (showLoader) {
      yield put(setGeneralLoaderVisibility(false));
    }
  }
}

export const updateUserAsync = (body: IUpdateUserRequest) =>
  editProfile(body)
    .then((authUser) => authUser)
    .catch((error) => error);

export function* editCurrentProfile({ payload }: TEditUser) {
  try {
    const result: IUpdateUserResponse | void = yield call(updateUserAsync, payload);
    if (!result) {
      return;
    }
    NotificationManager.success({
      message: 'user-account.edit-profile-success',
    });
    yield put(editCurrentUserSuccess(mapToCamelCase(result) as TUpdateUserMappedResponse));
  } catch (err) {
    yield put(profileEditFailed());
    NotificationManager.error({ message: 'user-account.edit-account-fail' });
    logger.error('edit profile error', err);
  }
}

export function* editCurrentAccount({ payload }: TEditAccount) {
  try {
    const result: IUpdateAccountResponse | void = yield call(editAccount, payload);
    if (!result) {
      yield put(accountEditFailed());
      NotificationManager.error({
        message: 'user-account.edit-account-fail',
      });

      return;
    }

    NotificationManager.success({
      message: 'user-account.edit-account-success',
    });
    yield put(editCurrentAccountSuccess(result));
  } catch (err) {
    NotificationManager.error({ message: 'user-account.edit-account-fail' });
    logger.error('account edit error', err);
  }
}

export function* sendPasswordReset({ payload }: TSendForgotPassword) {
  try {
    yield call(resetPassword, payload);
    NotificationManager.success({
      message: 'Email with reset instructions was sent',
    });
    yield put(sendForgotPasswordSuccess());
  } catch (e) {
    const message = getErrorMessage(e);
    logger.error(message, e);
    NotificationManager.error({ message });
    yield put(sendForgotPasswordFail());
  }
}

export function* sendPasswordChange({ payload }: TSendChangePassword) {
  try {
    const { token }: IChangePasswordResponse = yield call(changePassword, payload);
    NotificationManager.success({
      message: 'user-account.change-password-success',
    });
    yield put(setUserToken(token));
    yield put(sendChangePasswordSuccess());
  } catch (e) {
    const errorMessages = getErrorMessage(e);
    logger.error(errorMessages, e);
    NotificationManager.error({ message: errorMessages });
    yield put(sendChangePasswordFail());
  }
}

const resetPasswordSetAsync = (body: IConfirmResetPassword) =>
  resetPasswordSet(body)
    .then((data) => data)
    .catch((e) => e);

export function* sendPasswordResetConfirm({ payload }: TSendResetPassword) {
  try {
    const loginUser: IResetPasswordSetResponse = yield call(resetPasswordSetAsync, payload);
    setJwtCookie(loginUser.token);
    yield put(sendResetPasswordSuccess(loginUser));
    window.location.replace(ERoutes.Main);
  } catch (e) {
    logger.error(e);
    yield put(sendResetPasswordFail());
  }
}

export function handleSetUserToken({ payload }: TSetUserToken) {
  setJwtCookie(payload);
}

export function* fetchResendVerification() {
  try {
    yield resendVerification();
    NotificationManager.success({ message: 'dashboard.resend-verification' });
  } catch (e) {
    logger.error(e);
    NotificationManager.error({ message: getErrorMessage(e) });
  }
}

export function* handleUploadUserPhoto({ payload: { photo, onComplete } }: TUploadUserPhoto) {
  try {
    const {
      authUser: {
        account: { id },
      },
    }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);
    yield put(setGeneralLoaderVisibility(true));
    const [value]: TUploadedFile[] = yield uploadUserAvatar(photo, id!);

    if (value?.url) {
      yield call(changePhotoProfile, { photo: value.url });
      yield put(setUserPhoto(value.url));
      onComplete?.();
    }
  } catch (error) {
    logger.error('failed to upload user photo', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* handleDeleteUserPhoto() {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield call(changePhotoProfile, { photo: '' });
    yield put(setUserPhoto(''));
  } catch (error) {
    logger.error('failed to delete user photo', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* handleWatchUserWSEvents() {
  yield all([fork(watchNewTask), fork(watchRemoveTask), fork(watchNewNotifications), fork(watchNewWorkflowsEvent)]);
}

export function handleSetRedirectUrl({ payload: redirectUrl }: TSetRedirectUrl) {
  sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, redirectUrl);
}

export function* collectPaymentDetailsSaga() {
  const {
    authUser: {
      account: { paymentCardProvided },
    },
  }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);

  if (paymentCardProvided) {
    history.push(ERoutes.Tasks);

    return;
  }

  yield put(
    makeStripePayment({
      successUrl: getAbsolutePath(ERoutes.AfterPaymentDetailsProvided, { after_registration: 'true' }),
      cancelUrl: getAbsolutePath(ERoutes.Login),
      code: 'unlimited_month',
      showLoader: false,
    }),
  );
}

export function* changePaymentDetailsSaga() {
  try {
    yield put(setGeneralLoaderVisibility(true));

    const response: ICardSetupResponse = yield call(cardSetup, {
      successUrl: getAbsolutePath(ERoutes.AfterPaymentDetailsProvided, { new_payment_details: 'true' }),
      cancelUrl: getAbsolutePath(ERoutes.Main),
    });

    if (response.setupLink) {
      window.location.replace(response.setupLink);

      return;
    }

    yield put(setGeneralLoaderVisibility(false));
  } catch (error) {
    logger.error(error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

export function* makeStripePaymentSaga({
  payload: { successUrl, cancelUrl, code, quantity = 1, showLoader = true },
}: TMakeStripePayment) {
  try {
    if (showLoader) {
      yield put(setGeneralLoaderVisibility(true));
    }

    const response: IMakePaymentResponse = yield call(makePayment, {
      successUrl,
      cancelUrl,
      code,
      quantity,
    });

    if (response.paymentLink) {
      window.location.replace(response.paymentLink);

      return;
    }

    yield fetchPlan();
    yield authenticateUser();

    if (showLoader) {
      yield put(setGeneralLoaderVisibility(false));
    }

    history.push(ERoutes.Tasks);
    NotificationManager.success({ message: 'checkout.payment-success-title' });
  } catch (error) {
    if (showLoader) {
      yield put(setGeneralLoaderVisibility(false));
    }

    logger.error(error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

export function* onAfterPaymentDetailsProvidedSaga() {
  yield confirmPaymentDetailsProvided();

  const { after_registration: afterRegistrationParam, new_payment_details: newPaymentDetailsParam } =
    getQueryStringParams(history.location.search);

  if (newPaymentDetailsParam) {
    history.push(ERoutes.Main);

    return;
  }

  if (!afterRegistrationParam) {
    history.push(ERoutes.Tasks);

    return;
  }

  const { env } = getBrowserConfig();
  if (env === 'prod') {
    trackCrozdesk();
  }

  try {
    const templateId: Pick<ITemplate, 'name'> = yield createTemplateFromName();

    if (templateId) {
      history.push(ERoutes.TemplatesEdit.replace(':id', String(templateId)));
      return;
    }

    yield createAITemplate();
    history.push(ERoutes.Templates);
  } catch (error) {
    history.push(ERoutes.Templates);
  }
}

function* redirectToCustomerPortalSaga() {
  try {
    yield put(setGeneralLoaderVisibility(true));

    const { link } = yield call(getCustomerPortalLink, encodeURIComponent(window.location.href));

    if (link) {
      window.location.replace(link);

      return;
    }

    yield put(setGeneralLoaderVisibility(false));
  } catch (error) {
    yield put(setGeneralLoaderVisibility(false));
    logger.error(error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

export function* watchAuthUser() {
  yield takeEvery(EAuthActions.AuthUser, authUserSaga);
}

export function* watchEditUser() {
  yield takeEvery(EAuthActions.EditUser, editCurrentProfile);
}

export function* watchRegisterUser() {
  yield takeEvery(EAuthActions.RegisterUser, registerWithEmailPassword);
}

export function* watchRegisterUserInvited() {
  yield takeEvery(EAuthActions.RegisterUserInvited, registerWithInvite);
}

export function* watchLoginUser() {
  yield takeEvery(EAuthActions.LoginUser, loginWithEmailPassword);
}

export function* watchLoginSuperuser() {
  yield takeEvery(EAuthActions.LoginSuperuser, loginSuperuser);
}

export function* watchLoginPartnerSuperuser() {
  yield takeEvery(EAuthActions.LoginPartnerSuperuser, loginPartnerSuperuser);
}

export function* watchLogoutUser() {
  yield takeLeading(EAuthActions.LogoutUser, logout);
}

export function* watchChangePassword() {
  yield takeEvery(EAuthActions.ChangePassword, sendPasswordChange);
}

export function* watchForgotPassword() {
  yield takeEvery(EAuthActions.ForgotPassword, sendPasswordReset);
}

export function* watchResetPassword() {
  yield takeEvery(EAuthActions.ResetPassword, sendPasswordResetConfirm);
}

export function* watchEditAccount() {
  yield takeEvery(EAuthActions.EditAccount, editCurrentAccount);
}

export function* watchResendVerification() {
  yield takeLatest(EAuthActions.ResendVerification, fetchResendVerification);
}

export function* watchSetRedirectUrl() {
  yield takeLatest(EAuthActions.SetRedirectUrl, handleSetRedirectUrl);
}

export function* watchSetUserToken() {
  yield takeEvery(EAuthActions.SetToken, handleSetUserToken);
}

export function* watchUserWSEvents() {
  yield takeEvery(EAuthActions.WatchUserWSEvents, handleWatchUserWSEvents);
}

export function* watchUploadUserPhoto() {
  yield takeEvery(EAuthActions.UploadUserPhoto, handleUploadUserPhoto);
}

export function* watchDeleteUserPhoto() {
  yield takeEvery(EAuthActions.DeleteUserPhoto, handleDeleteUserPhoto);
}

export function* watchReturnFromSupermode() {
  yield takeEvery(EAuthActions.ReturnFromSupermode, retrunFromSupermodeSaga);
}

export function* watchCollectPaymentDetails() {
  yield takeEvery(EAuthActions.CollectPaymentDetails, collectPaymentDetailsSaga);
}

export function* watchChangePaymentDetails() {
  yield takeEvery(EAuthActions.ChangePaymentDetails, changePaymentDetailsSaga);
}

export function* watchMakeStripePayment() {
  yield takeEvery(EAuthActions.MakeStripePayment, makeStripePaymentSaga);
}

export function* watchOnAfterPaymentDetailsProvided() {
  yield takeEvery(EAuthActions.OnAfterPaymentDetailsProvided, onAfterPaymentDetailsProvidedSaga);
}

export function* watchRedirectToCustomerPortal() {
  yield takeEvery(EAuthActions.RedirectToCustomerPortal, redirectToCustomerPortalSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoginUser),
    fork(watchLoginSuperuser),
    fork(watchLoginPartnerSuperuser),
    fork(watchLogoutUser),
    fork(watchRegisterUser),
    fork(watchRegisterUserInvited),
    fork(watchAuthUser),
    fork(watchChangePassword),
    fork(watchEditAccount),
    fork(watchEditUser),
    fork(watchForgotPassword),
    fork(watchResetPassword),
    fork(watchResendVerification),
    fork(watchSetRedirectUrl),
    fork(watchSetUserToken),
    fork(watchUserWSEvents),
    fork(watchUploadUserPhoto),
    fork(watchDeleteUserPhoto),
    fork(watchReturnFromSupermode),
    fork(watchCollectPaymentDetails),
    fork(watchChangePaymentDetails),
    fork(watchMakeStripePayment),
    fork(watchOnAfterPaymentDetailsProvided),
    fork(watchRedirectToCustomerPortal),
  ]);
}
