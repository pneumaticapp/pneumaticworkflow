/* eslint-disable class-methods-use-this */
import { getToken } from './getToken';
import { NotificationManager } from '../components/UI/Notifications';
import { registerUser } from './registerUser';
import { getUser } from './getUser';
import { IUnsavedUser, TUserInvited } from '../types/user';
import { getErrorMessage } from '../utils/getErrorMessage';
import { IAuthUser } from '../types/redux';
import { acceptInvite } from './acceptInvite';
import { IUserRegister } from '../redux/auth/actions';
import { logger } from '../utils/logger';
import { IUserUtm } from '../views/user/utils/utmParams';
import { ESubscriptionPlan } from '../types/account';

import { getTokenAsSuperuser } from './getTokenAsSuperuser';

const ERR_REGISTER_MSG = 'Register failed';
const SUCCESS_REGISTER_MSG = 'Your account was successfully registered';
const EMPTY_USER_DATA: IUnsavedUser = {
  email: '',
  token: '',
  firstName: '',
  lastName: '',
  phone: '',
  account: {
    name: '',
    tenantName: '',
    billingPlan: ESubscriptionPlan.Unknown,
    plan: ESubscriptionPlan.Unknown,
    planExpiration: null,
    leaseLevel: 'standard',
    logoSm: null,
    logoLg: null,
    paymentCardProvided: true,
    trialEnded: false,
    trialIsActive: false,
    isSubscribed: false
  },
  photo: '',
  type: 'user',
  language: '',
  timezone: '',
  dateFmt: '',
  dateFdw: ''
};

class AuthCreator {
  public signInWithEmailAndPassword = async (email: string, password: string): Promise<IUnsavedUser> => {
    try {
      const result = await getToken(email, password);
      const user = await getUser(result?.token);

      return {
        ...(user || EMPTY_USER_DATA),
        email,
        token: result?.token || '',
      };
    } catch (e) {
      const message = getErrorMessage(e);
      throw new Error(message);
    }
  };

  public signInAsSuperuser = async (email: string) => {
    const result = await getTokenAsSuperuser(email);

    return {
      ...EMPTY_USER_DATA,
      email,
      token: result?.token || '',
    };
  };

  public createUserWithEmail = async (
    user: IUserRegister,
    utmParams?: IUserUtm,
    captcha?: string,
  ): Promise<Partial<IAuthUser>> => {
    try {
      const result = await registerUser(user, utmParams, captcha);

      if (!result) {
        NotificationManager.error({ message: ERR_REGISTER_MSG });
        throw new Error(ERR_REGISTER_MSG);
      }

      return {
        loading: false,
        token: result.token,
      };
    } catch (err) {
      throw new Error(getErrorMessage(err));
    }
  };

  public createUserWithInvite = async (id: string, user: TUserInvited): Promise<Partial<IAuthUser>> => {
    try {
      const result = await acceptInvite(id, user);

      if (!result) {
        throw new Error(ERR_REGISTER_MSG);
      }

      NotificationManager.success({ message: SUCCESS_REGISTER_MSG });

      return {
        loading: false,
        token: result.token,
      };
    } catch (err) {
      throw new Error(getErrorMessage(err));
    }
  };

  public getUser = async () => {
    try {
      const result = await getUser();

      if (!result) {
        throw new Error('failed to fetch user data');
      }

      return result;
    } catch (err) {
      logger.error('failed to fetch user data ', err);
      NotificationManager.error({ message: 'user.fetch-failed' });

      throw new Error('failed to fetch user data');
    }
  };
}

export const auth = new AuthCreator();
