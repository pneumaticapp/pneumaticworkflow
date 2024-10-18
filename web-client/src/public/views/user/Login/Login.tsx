import React, { useEffect } from 'react';
import { Formik, FormikConfig } from 'formik';
import { useIntl } from 'react-intl';

import { EOAuthType } from '../../../types/auth';
import { ERoutes } from '../../../constants/routes';
import { TITLES } from '../../../constants/titles';
import { getOAuthUrl } from '../../../api/getGoogleAuthUrl';
import { IntlMessages } from '../../../components/IntlMessages';
import { IUserCredentials, EAuthUserFailType } from '../../../redux/actions';
import { NavLink } from '../../../components/NavLink';
import { validateEmail, validatePassword } from '../../../utils/validators';
import { getQueryStringParams, history } from '../../../utils/history';
import { Button, FormikCheckbox, Header, InputField } from '../../../components/UI';
import { GoogleButton, MicrosoftButton } from '../../../components/OAuthButtons';
import { saveUTMParams } from '../utils/utmParams';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';
import { isEnvGoogleAuth, isEnvMsAuth, isEnvSSOAuth, isEnvSignup } from '../../../constants/enviroment';

import styles from '../User.css';

const INITIAL_VALUES_FORMIK: TLoginValues = {
  email: '',
  password: '',
  rememberMe: true,
};

export function Login({ loading, error, loginUser, setRedirectUrl }: ILoginProps) {
  const { formatMessage } = useIntl();

  useEffect(() => {
    const queryString = history.location.search;
    const queryParams = getQueryStringParams(queryString);
    const { redirectUrl = '' } = queryParams;

    setRedirectUrl(redirectUrl);
    saveUTMParams();

    document.title = TITLES.Login;
  }, []);

  const wrongCredentialsErrorMessage = () => {
    const shouldShowErrorMessage = [error, error !== EAuthUserFailType.NotVerified].every(Boolean);

    if (shouldShowErrorMessage) {
      return 'validation.login-invalid-email-or-password';
    }

    return '';
  };

  const handleOAuthSignInClick = (type: EOAuthType) => async (e: React.MouseEvent) => {
    e.preventDefault();

    const result = await getOAuthUrl(type);

    if (result && 'redirectUri' in result) {
      window.location.assign(result.redirectUri);
    }
  };

  const handleSubmitForm: FormikConfig<TLoginValues>['onSubmit'] = (values) => {
    const { email, password, rememberMe } = values;

    loginUser({ email, password, rememberMe });
  };

  return (
    <>
      <Header size="4" tag="h2" className={styles['title']}>
        <IntlMessages id="user.login-title" />
      </Header>

      <div className={styles['oauth']}>
        {isEnvGoogleAuth && (
          <GoogleButton
            label={formatMessage({ id: 'user.sign-up-google' })}
            onClick={handleOAuthSignInClick(EOAuthType.Google)}
            className={styles['oauth__button']}
          />
        )}
        {isEnvMsAuth && (
          <MicrosoftButton
            label={formatMessage({ id: 'user.sign-up-microsoft' })}
            onClick={handleOAuthSignInClick(EOAuthType.Microsoft)}
            className={styles['oauth__button']}
          />
        )}
      </div>

      {(isEnvGoogleAuth || isEnvMsAuth || isEnvSSOAuth) && (
        <div className={styles['divider']}>
          <p>
            <IntlMessages id="user.or" />
          </p>
        </div>
      )}

      <Formik
        initialValues={INITIAL_VALUES_FORMIK}
        onSubmit={handleSubmitForm}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            email: validateEmail,
            password: validatePassword,
          });

          return errors;
        }}
      >
        {({ values, errors, handleChange, handleSubmit, isValid, dirty }) => (
          <form className={styles['form']} onSubmit={handleSubmit}>
            <InputField
              name="email"
              type="email"
              title={formatMessage({ id: 'user.email' })}
              value={values.email}
              onChange={handleChange}
              errorMessage={errors.email}
              showErrorIfTouched
              data-test-id="input-login-email"
              containerClassName={styles['form__field']}
            />

            <InputField
              name="password"
              type="password"
              title={formatMessage({ id: 'user.password' })}
              value={values.password}
              onChange={handleChange}
              errorMessage={errors.password || wrongCredentialsErrorMessage()}
              showErrorIfTouched
              data-test-id="input-login-password"
              containerClassName={styles['form__field']}
              showPasswordVisibilityToggle
            />

            <div className={styles['form__settings']}>
              <FormikCheckbox
                title={formatMessage({ id: 'user.remember-me' })}
                name="rememberMe"
                containerClassName={styles['remember-me']}
              />

              <div className={styles['forgot-password']}>
                <NavLink to={ERoutes.ForgotPassword} className={styles['link']}>
                  <IntlMessages id="user.password-forgot" />
                </NavLink>
              </div>
            </div>

            <Button
              type="submit"
              buttonStyle="yellow"
              isLoading={loading}
              className={styles['form__submit']}
              size="lg"
              disabled={!isValid || !dirty}
              data-test-id="login-button"
              label={formatMessage({ id: 'user.login-button' })}
            />
          </form>
        )}
      </Formik>

      {isEnvSignup && (
        <div className={styles['footnote']}>
          <IntlMessages id="user.sign-in-not-a-member" />

          <NavLink to={ERoutes.Register} className={styles['link']}>
            <IntlMessages id="user.register-link" />
          </NavLink>
        </div>
      )}
    </>
  );
}

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
