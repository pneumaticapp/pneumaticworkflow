import { call } from "redux-saga/effects";
import { getQueryStringParams, history } from '../../../utils/history';
import { confirmPaymentDetails } from "../../../api/confirmPaymentDetails";
import { fetchPlan } from "../../accounts/saga";
import { authenticateUser } from "../saga";
import { logger } from "../../../utils/logger";
import { NotificationManager } from "../../../components/UI/Notifications";
import { getErrorMessage } from "../../../utils/getErrorMessage";
import { ERoutes } from "../../../constants/routes";

export const MESSAGE_BY_PARAM_MAP = {
  new_payment_details: 'checkout.card-setup',
  after_registration: 'checkout.payment-success-title',
  trial_started: 'pricing.switched-to-trial',
}

export function* confirmPaymentDetailsProvided() {
  try {
    if (!history.location.search) {
      throw new Error('No token provided');
    }
    const { token } = getQueryStringParams(history.location.search);
    if (!token) {
      throw new Error('No token provided');
    }
    yield call(confirmPaymentDetails, { token });
    yield fetchPlan();
    yield authenticateUser();
    showSuccessMessage();
  } catch (error) {
    logger.error(error);
    NotificationManager.error({ message: getErrorMessage(error) });
    history.push(ERoutes.Tasks);
  }
}

function showSuccessMessage() {
  const queryParams = getQueryStringParams(history.location.search);
  const [, message] = Object.entries(MESSAGE_BY_PARAM_MAP).find(([code]) => queryParams[code]) || [null, 'checkout.payment-success-title'];
  NotificationManager.success({ message });
}
