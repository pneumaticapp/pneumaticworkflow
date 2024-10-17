import React, { useEffect, useState } from 'react';
import { Field, Formik, FormikConfig } from 'formik';
import { useIntl } from 'react-intl';
import ReCAPTCHA from 'react-google-recaptcha';
import moment from 'moment-timezone';

import { TRegisterUserPayload } from '../../../redux/actions';
import { IntlMessages } from '../../../components/IntlMessages';
import { ERoutes } from '../../../constants/routes';
import { TITLES } from '../../../constants/titles';
import { validateEmail, validateName, validatePhone, validateRegistrationPassword } from '../../../utils/validators';
import { getOAuthUrl } from '../../../api/getGoogleAuthUrl';
import { getQueryStringParams, history } from '../../../utils/history';
import { EOAuthType } from '../../../types/auth';
import { NavLink } from '../../../components/NavLink';
import { saveUTMParams } from '../utils/utmParams';
import { prepareRegisterUser } from '../../../api/prepareRegisterUser';
import { getBrowserConfigEnv } from '../../../utils/getConfig';
import { setLandingTemplate } from '../../../utils/landingTemplate';
import { setTemplateName } from './utils/templateName';
import { Button, Header, InputField } from '../../../components/UI';
import { GoogleButton, MicrosoftButton } from '../../../components/OAuthButtons';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';
import { Phone } from '../../../components/UI/FormikFields';
import { isEnvCaptcha, isEnvGoogleAuth, isEnvMsAuth, isEnvSSOAuth } from '../../../constants/enviroment';
import { TIMEZONE_OFFSET_MAP } from '../../../constants/profile';

import styles from '../User.css';
import 'react-phone-number-input/style.css';

const INITIAL_VALUES_FORMIK: TRegisterValues = {
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  phone: '',
  captcha: '',
};

export function Register({ registerUser }: IRegisterProps) {
  const { formatMessage } = useIntl();
  const { reсaptchaSecret } = getBrowserConfigEnv();
  const [showCaptcha, setShowCaptcha] = useState(false);
  const defaultOffset = moment().utcOffset();

  useEffect(() => {
    document.title = TITLES.Register;
    saveUTMParams();

    if (isEnvCaptcha) {
      checkCaptchaNeeded();
    }

    const { template, template_name: templateName } = getQueryStringParams(history.location.search);

    if (templateName) {
      setTemplateName(templateName);
    }

    if (template) {
      setLandingTemplate(template);
    }
  }, []);

  const checkCaptchaNeeded = async () => {
    const prepareResult = await prepareRegisterUser();

    if (prepareResult || prepareResult!.showCaptcha) {
      setShowCaptcha(true);
    }
  };

  const handleSubmitForm: FormikConfig<TRegisterValues>['onSubmit'] = (values, { setSubmitting }) => {
    const { firstName, lastName, email, password, phone, captcha } = values;

    registerUser({
      captcha,
      user: {
        firstName,
        lastName,
        email,
        photo: '',
        ...(phone && { phone }),
        fromEmail: true,
        password,
        timezone: TIMEZONE_OFFSET_MAP[defaultOffset]
      },
      onStart: () => setSubmitting(true),
      onFinish: () => setSubmitting(false),
    });
  };

  const handleOAuthSignUpClick = (type: EOAuthType) => async (e: React.MouseEvent) => {
    e.preventDefault();

    const result = await getOAuthUrl(type);

    if (result && 'redirectUri' in result) {
      window.location.assign(result.redirectUri);
    }
  };

  return (
    <>
      <Header size="4" tag="h2" className={styles['title']}>
        <IntlMessages id="user.register-title" />
      </Header>

      <div className={styles['oauth']}>
        {isEnvGoogleAuth && (
          <GoogleButton
            label={formatMessage({ id: 'user.sign-up-google' })}
            onClick={handleOAuthSignUpClick(EOAuthType.Google)}
            className={styles['oauth__button']}
          />
        )}
        {isEnvMsAuth && (
          <MicrosoftButton
            label={formatMessage({ id: 'user.sign-up-microsoft' })}
            onClick={handleOAuthSignUpClick(EOAuthType.Microsoft)}
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
            firstName: validateName,
            lastName: validateName,
            email: validateEmail,
            phone: validatePhone,
            password: validateRegistrationPassword,
          });

          if (showCaptcha && !values.captcha) {
            errors.captcha = 'Failed verification captcha';
          }

          return errors;
        }}
      >
        {({ values, errors, handleChange, handleSubmit, setFieldValue, isSubmitting, isValid, dirty }) => (
          <form className={styles['form']} onSubmit={handleSubmit}>
            <InputField
              name="firstName"
              value={values.firstName}
              onChange={handleChange}
              errorMessage={errors.firstName}
              title={formatMessage({ id: 'user.first-name' })}
              data-test-id="input-user-first-name"
              containerClassName={styles['form__field']}
              showErrorIfTouched
            />
            <InputField
              name="lastName"
              value={values.lastName}
              onChange={handleChange}
              title={formatMessage({ id: 'user.last-name' })}
              errorMessage={errors.lastName}
              data-test-id="input-user-last-name"
              containerClassName={styles['form__field']}
              showErrorIfTouched
            />
            <InputField
              name="email"
              value={values.email}
              onChange={handleChange}
              title={formatMessage({ id: 'user.email-work' })}
              errorMessage={errors.email}
              data-test-id="input-registration-email"
              containerClassName={styles['form__field']}
              showErrorIfTouched
            />
            <div className={styles['form__field']}>
              <Field
                name="phone"
                component={Phone}
                title={formatMessage({ id: 'user.phone' })}
                tooltipText={formatMessage({ id: 'user.phone-tooltip' })}
                errorMessage={errors.phone}
              />
            </div>

            <InputField
              name="password"
              value={values.password}
              onChange={handleChange}
              title={formatMessage({ id: 'user.password' })}
              errorMessage={errors.password}
              data-test-id="input-registration-password"
              containerClassName={styles['form__field']}
              showErrorIfTouched
              showPasswordVisibilityToggle
            />

            {(isEnvCaptcha && showCaptcha) && (
              <div className={styles['form__captcha']}>
                <ReCAPTCHA
                  sitekey={reсaptchaSecret}
                  onChange={(captcha: string | null) => captcha && setFieldValue('captcha', captcha)}
                  theme="light"
                />
              </div>
            )}

            <p className={styles['form__terms']}>
              <IntlMessages
                id="user.you-agree-to-pneumatic-terms"
                values={{
                  termsOfService: (
                    <a
                      href="https://www.pneumatic.app/legal/terms/"
                      target="_blank"
                      className={styles['link']}
                      rel="noreferrer"
                    >
                      <span>{formatMessage({ id: 'user.register-terms-link' })}</span>
                    </a>
                  ),
                }}
              />
            </p>

            <Button
              buttonStyle="yellow"
              isLoading={isSubmitting}
              className={styles['form__submit']}
              size="lg"
              type="submit"
              disabled={!isValid || !dirty}
              data-test-id="registration-button"
              label={formatMessage({ id: 'user.register-button' })}
            />
          </form>
        )}
      </Formik>

      <div className={styles['footnote']}>
        <IntlMessages id="user.register-already" />

        <NavLink to={ERoutes.Login} className={styles['link']}>
          <IntlMessages id="user.login-link" />
        </NavLink>
      </div>
    </>
  );
}

export interface IRegisterProps {
  registerUser(payload: TRegisterUserPayload): void;
}

export type TRegisterValues = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  password: string;
  captcha: string;
};
