import { getQueryStringParams, history } from '../../../utils/history';
import { NotificationManager } from '../../../components/UI/Notifications';

const MESSAGE_BY_PARAM_MAP = {
  new_payment_details: 'checkout.card-setup',
  after_registration: 'checkout.payment-success-title',
  trial_started: 'pricing.switched-to-trial',
};

export function showPaymentSuccessMessage() {
  const queryParams = getQueryStringParams(history.location.search);
  const [, message] = Object.entries(MESSAGE_BY_PARAM_MAP).find(([code]) => queryParams[code]) || [
    null,
    'checkout.payment-success-title',
  ];
  NotificationManager.success({ message });
}
