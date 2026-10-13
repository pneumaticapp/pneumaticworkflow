import * as React from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';

import { ERoutes } from '../../../constants/routes';
import { IntlMessages } from '../../../components/IntlMessages';
import { EAuthUserFailType } from '../../../redux/actions';
import { NavLink } from '../../../components/NavLink';
import { validateEmail, validatePassword } from '../../../utils/validators';
import { Button, FormikCheckbox, Header, InputField } from '../../../components/UI';
import { GoogleButton, MicrosoftButton, SSOButton } from '../../../components/OAuthButtons';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';
import { isEnvGoogleAuth, isEnvMsAuth, isEnvSSOAuth, isEnvSignup } from '../../../constants/enviroment';
import { ILoginProps, TLoginValues } from './types';

import { useLogin } from './useLogin';
import styles from '../User.css';

const INITIAL_VALUES_FORMIK: TLoginValues = {
  email: '',
  password: '',
  rememberMe: true,
};

export function Login({ loading, error, loginUser, setRedirectUrl }: ILoginProps) {
  const { formatMessage } = useIntl();
  const { handleGoogleSignIn, handleMicrosoftSignIn, handleSSOSignIn, handleSubmitForm, oauthBusy, oauthError } =
    useLogin({ loginUser, setRedirectUrl });

  const wrongCredentialsErrorMessage = () => {
    const shouldShowErrorMessage = [error, error !== EAuthUserFailType.NotVerified].every(Boolean);

    if (shouldShowErrorMessage) {
      return 'validation.login-invalid-email-or-password';
    }

    return '';
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
            onClick={handleGoogleSignIn}
            disabled={oauthBusy}
            className={styles['oauth__button']}
          />
        )}
        {isEnvMsAuth && (
          <MicrosoftButton
            label={formatMessage({ id: 'user.sign-up-microsoft' })}
            onClick={handleMicrosoftSignIn}
            disabled={oauthBusy}
            className={styles['oauth__button']}
          />
        )}
        {isEnvSSOAuth && (
          <SSOButton
            label={formatMessage({ id: 'user.sign-up-sso' })}
            onClick={handleSSOSignIn}
            disabled={oauthBusy}
            className={styles['oauth__button']}
          />
        )}
      </div>

      {oauthError && <p role="alert">{formatMessage({ id: oauthError })}</p>}

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
