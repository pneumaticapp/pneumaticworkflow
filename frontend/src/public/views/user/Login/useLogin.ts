import { MouseEvent, useCallback, useEffect, useRef, useState } from 'react';
import { FormikConfig } from 'formik';
import { useLocation } from 'react-router-dom';
import { EOAuthType } from '../../../types/auth';
import { TITLES } from '../../../constants/titles';
import { getOAuthUrl } from '../../../api/getGoogleAuthUrl';
import { getQueryStringParams } from '../../../utils/history';
import { getBrowserConfigEnv } from '../../../utils/getConfig';
import { mcpContinuation, safeRedirect } from '../../../utils/safeRedirect';
import { REDIRECT_URL_STORAGE_KEY } from '../../../constants/storageKeys';
import { envSSOProvider } from '../../../constants/enviroment';
import { SSOProvider } from '../../../../server/types';
import { saveUTMParams } from '../utils/utmParams';
import { ILoginProps, TLoginValues } from './types';

export function useLogin({ loginUser, setRedirectUrl }: Pick<ILoginProps, 'loginUser' | 'setRedirectUrl'>) {
  const { search } = useLocation();
  const controller = useRef<AbortController>();
  const authorizing = useRef(false);
  const [oauthBusy, setOAuthBusy] = useState(false);
  const [oauthError, setOAuthError] = useState('');
  const typeSSOProvider = envSSOProvider === SSOProvider.Auth0 ? EOAuthType.SSOAuth0 : EOAuthType.SSOOkta;

  useEffect(() => {
    const requestController = new AbortController();
    controller.current = requestController;
    authorizing.current = false;
    setOAuthBusy(false);
    setOAuthError('');
    const { redirectUrl = '' } = getQueryStringParams(search);
    const target =
      safeRedirect(redirectUrl, getBrowserConfigEnv().api?.fileServiceUrl) ||
      mcpContinuation(sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY));
    setRedirectUrl(target);
    saveUTMParams();
    const previousTitle = document.title;
    document.title = TITLES.Login;
    return () => {
      requestController.abort();
      document.title = previousTitle;
    };
  }, [search, setRedirectUrl]);

  const handleOAuthSignIn = useCallback(async (type: EOAuthType, event: MouseEvent) => {
    event.preventDefault();
    const signal = controller.current?.signal;
    if (authorizing.current || !signal || signal.aborted) return;
    authorizing.current = true;
    setOAuthBusy(true);
    setOAuthError('');
    let redirected = false;
    try {
      const continuation = mcpContinuation(sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY));
      const result = await getOAuthUrl(type, continuation || undefined);
      if (signal.aborted) return;
      if (result && 'redirectUri' in result && typeof result.redirectUri === 'string' && result.redirectUri) {
        window.location.assign(result.redirectUri);
        redirected = true;
      } else setOAuthError('user.oauth-unavailable');
    } catch {
      if (!signal.aborted) setOAuthError('user.oauth-unavailable');
    } finally {
      if (!signal.aborted && !redirected) {
        authorizing.current = false;
        setOAuthBusy(false);
      }
    }
  }, []);
  const handleGoogleSignIn = useCallback(
    (event: MouseEvent) => {
      void handleOAuthSignIn(EOAuthType.Google, event);
    },
    [handleOAuthSignIn],
  );
  const handleMicrosoftSignIn = useCallback(
    (event: MouseEvent) => {
      void handleOAuthSignIn(EOAuthType.Microsoft, event);
    },
    [handleOAuthSignIn],
  );
  const handleSSOSignIn = useCallback(
    (event: MouseEvent) => {
      void handleOAuthSignIn(typeSSOProvider, event);
    },
    [handleOAuthSignIn, typeSSOProvider],
  );
  const handleSubmitForm = useCallback<FormikConfig<TLoginValues>['onSubmit']>(
    (values) => {
      const { email, password, rememberMe } = values;
      loginUser({ email, password, rememberMe });
    },
    [loginUser],
  );

  return { handleGoogleSignIn, handleMicrosoftSignIn, handleSSOSignIn, handleSubmitForm, oauthBusy, oauthError };
}
