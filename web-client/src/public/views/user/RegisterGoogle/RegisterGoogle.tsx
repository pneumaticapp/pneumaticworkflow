import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import ReCAPTCHA from 'react-google-recaptcha';
import moment from 'moment-timezone';

import { TRegisterUserPayload } from '../../../redux/actions';
import { NotificationManager } from '../../../components/UI/Notifications';
import { IntlMessages } from '../../../components/IntlMessages';
import { ERoutes } from '../../../constants/routes';
import { TITLES } from '../../../constants/titles';
import { TGoogleAuthUserInfo } from '../../../types/user';
import { GoogleProfile } from '../GoogleProfile';
import { isGoogleAuth, getQueryStringParams, history } from '../../../utils/history';
import { NavLink } from '../../../components/NavLink';
import { trackGoogleRegistration } from '../../../utils/analytics';
import { saveUTMParams } from '../utils/utmParams';
import { prepareRegisterUser } from '../../../api/prepareRegisterUser';
import { getBrowserConfigEnv } from '../../../utils/getConfig';
import { setLandingTemplate } from '../../../utils/landingTemplate';
import { Button, Header } from '../../../components/UI';
import { isEnvCaptcha } from '../../../constants/enviroment';
import { TIMEZONE_OFFSET_MAP } from '../../../constants/profile';

import styles from '../User.css';

export function RegisterGoogle({ googleAuthUserInfo, registerUser, removeGoogleUser }: IRegisterGoogleProps) {
  const { formatMessage } = useIntl();
  const { reсaptchaSecret } = getBrowserConfigEnv();
  const isGoogle = isGoogleAuth();
  const preloadedUserInfo = (): TGoogleAuthUserInfo => {
    return (isGoogle && googleAuthUserInfo) || {};
  };
  const defaultOffset = moment().utcOffset();

  const userInfo = preloadedUserInfo();

  const [captcha, setCaptcha] = useState('');
  const [showCaptcha, setShowCaptcha] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    document.title = TITLES.Register;
    trackGoogleRegistration();
    saveUTMParams();
    if (isEnvCaptcha) checkCaptchaNeeded();

    const { template } = getQueryStringParams(history.location.search);

    if (template) {
      setLandingTemplate(template);
    }

    return () => {
      removeGoogleUser();
    };
  }, []);

  const checkCaptchaNeeded = async () => {
    const prepareResult = await prepareRegisterUser();

    if (!prepareResult || !prepareResult.showCaptcha) {
      return;
    }

    setShowCaptcha(true);
  };

  const onUserRegister = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (isFormValid()) {
      const photo = preloadedUserInfo().photo || '';
      const companyName = preloadedUserInfo().companyName || '';

      registerUser({
        captcha,
        user: {
          email: userInfo.email!,
          firstName: userInfo.firstName!,
          lastName: userInfo.lastName!,
          photo,
          fromEmail: false,
          timezone: TIMEZONE_OFFSET_MAP[defaultOffset],
          ...(companyName && { companyName }),
        },
        onStart: () => setIsLoading(true),
        onFinish: () => setIsLoading(false),
      });
    } else {
      NotificationManager.warning({ message: <IntlMessages id="user.register-required-fields" /> });
    }
  };

  const isFormValid = () => {
    return !showCaptcha || Boolean(captcha);
  };

  const isSubmitButtonDisabled = !isFormValid();

  return (
    <>
      <Header size="4" tag="h2" className={styles['title']}>
        <IntlMessages id="user.register-title-google" />
      </Header>

      {isGoogle && <GoogleProfile {...userInfo} />}
      <form className={styles['form']} onSubmit={onUserRegister}>
        {isEnvCaptcha && showCaptcha && (
          <div className={styles['captcha']}>
            <ReCAPTCHA
              sitekey={reсaptchaSecret}
              onChange={(captchaLocal: string | null) => captchaLocal && setCaptcha(captchaLocal)}
              theme="light"
            />
          </div>
        )}

        <p className={styles['terms']}>
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
          isLoading={isLoading}
          className={styles['form__submit']}
          size="lg"
          type="submit"
          disabled={isSubmitButtonDisabled}
          data-test-id="registration-button"
          label={formatMessage({ id: 'user.register-button' })}
        />
      </form>

      <div className={styles['footnote']}>
        <IntlMessages id="user.register-already" />

        <NavLink to={ERoutes.Login} className={styles['link']}>
          <IntlMessages id="user.login-link" />
        </NavLink>
      </div>
    </>
  );
}

export interface IRegisterGoogleProps {
  googleAuthUserInfo: TGoogleAuthUserInfo;
  registerUser(payload: TRegisterUserPayload): void;
  removeGoogleUser(): void;
}
