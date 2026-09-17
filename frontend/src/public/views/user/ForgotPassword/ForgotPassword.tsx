import React, { useEffect, useRef, useState } from 'react';
import { Formik, FormikConfig, useFormikContext } from 'formik';
import { NavLink } from 'react-router-dom';
import { useIntl } from 'react-intl';
import ReCAPTCHA from 'react-google-recaptcha';

import { ERoutes } from '../../../constants/routes';
import { TITLES } from '../../../constants/titles';
import { IntlMessages } from '../../../components/IntlMessages';
import { validateEmail } from '../../../utils/validators';
import { Header, InputField, Button } from '../../../components/UI';
import { getResetPasswordCaptcha } from '../../../api/getResetPasswordCaptcha';
import { getBrowserConfigEnv } from '../../../utils/getConfig';
import { logger } from '../../../utils/logger';

import styles from '../User.css';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';
import { isEnvCaptcha, isEnvSignup } from '../../../constants/enviroment';

import { ICaptchaFieldProps, IForgotPasswordProps, TForgotPasswordValues } from './types';

const INITIAL_VALUES_FORMIK: TForgotPasswordValues = {
  email: '',
  captcha: '',
};

export function ForgotPassword({ loading, sendForgotPassword }: IForgotPasswordProps) {
  const { formatMessage } = useIntl();
  const [showCaptcha, setShowCaptcha] = useState(false);
  const [isCheckingCaptcha, setIsCheckingCaptcha] = useState(isEnvCaptcha);
  const [captchaResetSignal, setCaptchaResetSignal] = useState(0);
  const prevLoadingRef = useRef(loading);

  useEffect(() => {
    document.title = TITLES.ForgotPassword;

    if (isEnvCaptcha) {
      checkCaptchaNeeded();
    }
  }, []);

  useEffect(() => {
    if (isEnvCaptcha && prevLoadingRef.current && !loading) {
      checkCaptchaNeeded();
      // captcha tokens are single-use: force a fresh challenge for a retry
      setCaptchaResetSignal((signal) => signal + 1);
    }
    prevLoadingRef.current = loading;
  }, [loading]);

  const checkCaptchaNeeded = async () => {
    setIsCheckingCaptcha(true);

    try {
      const result = await getResetPasswordCaptcha();

      if (result?.showCaptcha) {
        setShowCaptcha(true);
      }
    } catch (error) {
      logger.error('check reset password captcha error', error);
    } finally {
      setIsCheckingCaptcha(false);
    }
  };

  const handleSubmitForm: FormikConfig<TForgotPasswordValues>['onSubmit'] = (values) => {
    const { email, captcha } = values;

    sendForgotPassword({ email, captcha });
  };

  return (
    <>
      <Header size="4" tag="h2" className={styles['title']}>
        <IntlMessages id="user.password-forgot-title" />
      </Header>

      <Formik
        initialValues={INITIAL_VALUES_FORMIK}
        onSubmit={handleSubmitForm}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            email: validateEmail,
          });

          if (showCaptcha && !values.captcha) {
            errors.captcha = 'Failed verification captcha';
          }

          return errors;
        }}
      >
        {({ values, errors, handleChange, handleSubmit, isValid, dirty }) => (
          <form className={styles['form']} onSubmit={handleSubmit}>
            <InputField
              name="email"
              title={formatMessage({ id: 'user.email' })}
              value={values.email}
              onChange={handleChange}
              errorMessage={errors.email}
              showErrorIfTouched
              containerClassName={styles['form__field']}
            />

            {isEnvCaptcha && showCaptcha && <CaptchaField resetSignal={captchaResetSignal} />}

            <Button
              type="submit"
              buttonStyle="yellow"
              isLoading={loading}
              className={styles['form__submit']}
              size="lg"
              disabled={!isValid || !dirty || isCheckingCaptcha}
              label={formatMessage({ id: 'user.password-forgot-button' })}
            />
          </form>
        )}
      </Formik>

      <div className={styles['footnote']}>
        <NavLink to={ERoutes.Login} className={styles['link']}>
          <IntlMessages id="user.login-link" />
        </NavLink>

        {isEnvSignup && (
          <>
            <span>{formatMessage({ id: 'user.password-forgot-or' })}</span>
            <NavLink to={ERoutes.Register} className={styles['link']}>
              <IntlMessages id="user.register-link" />
            </NavLink>
          </>
        )}
      </div>
    </>
  );
}

function CaptchaField({ resetSignal }: ICaptchaFieldProps) {
  const { recaptchaSecret } = getBrowserConfigEnv();
  const { setFieldValue, validateForm } = useFormikContext<TForgotPasswordValues>();

  useEffect(() => {
    // Formik doesn't re-validate on external state changes
    validateForm();
  }, [validateForm]);

  useEffect(() => {
    if (resetSignal > 0) {
      setFieldValue('captcha', '');
    }
  }, [resetSignal, setFieldValue]);

  return (
    <div className={styles['form__captcha']}>
      <ReCAPTCHA
        key={resetSignal}
        sitekey={recaptchaSecret}
        onChange={(captcha: string | null) => setFieldValue('captcha', captcha || '')}
        theme="light"
      />
    </div>
  );
}
