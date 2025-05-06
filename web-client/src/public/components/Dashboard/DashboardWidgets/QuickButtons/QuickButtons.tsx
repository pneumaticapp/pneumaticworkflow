import React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { SectionTitle } from '../../../UI/Typeography/SectionTitle/SectionTitle';
import { analytics, EAnalyticsAction, EAnalyticsCategory } from '../../../../utils/analytics';
import { openSelectTemplateModal } from '../../../../redux/actions';
import { CircleWithArrowRightIcon } from '../../../icons';
import { ERoutes } from '../../../../constants/routes';
import { history } from '../../../../utils/history';

import styles from './QuickButtons.css';

interface IQuickButtonsProps {
  isAdmin: boolean;
  isTemplateOwner: undefined | boolean;
}
export function QuickButtons({ isAdmin, isTemplateOwner }: IQuickButtonsProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const createTemplateButton = {
    title: formatMessage({ id: 'dashboard.quick-button-create-template-title' }),
    description: formatMessage({ id: 'dashboard.quick-button-create-template-description' }),
    analyticsEventName: 'Add template',
    analyticsCategory: EAnalyticsCategory.Templates,
    analyticsLabel: QUICK_BUTTONS_ANALYTICS_LABEL,
    Icon: CircleWithArrowRightIcon,
    action: () => history.push(ERoutes.Templates),
  };

  const runWorkflowButton = {
    title: formatMessage({ id: 'dashboard.quick-button-run-workflow-title' }),
    description: formatMessage({ id: 'dashboard.quick-button-run-workflow-description' }),
    analyticsEventName: 'Run Workflow',
    analyticsCategory: EAnalyticsCategory.Workflow,
    analyticsLabel: QUICK_BUTTONS_ANALYTICS_LABEL,
    Icon: CircleWithArrowRightIcon,
    action: () => dispatch(openSelectTemplateModal()),
  };

  const handleCickButton = (button: TQuickButton) => () => {
    trackClickQuickButton(button);
    button.action();
  };

  let QUICK_BUTTONS: TQuickButton[] = [];
  if (isAdmin) {
    QUICK_BUTTONS = [createTemplateButton, runWorkflowButton];
  } else if (isTemplateOwner) {
    QUICK_BUTTONS = [runWorkflowButton];
  }
  if (QUICK_BUTTONS.length === 0) return null;

  return (
    <div className={styles['quick-button']}>
      <SectionTitle className={styles['quick-button__title']}>
        {formatMessage({ id: 'dashboard.quick-button-title' }, { br: <br /> })}
      </SectionTitle>

      {QUICK_BUTTONS.map((quickButton) => {
        const { title, description, Icon } = quickButton;

        return (
          <div className={styles['quick-button__item']} key={`${title}`}>
            <button type="button" onClick={handleCickButton(quickButton)} className={styles['item-quick-button']}>
              <h3 className={styles['item-quick-button__title']}>{title}</h3>
              <p className={styles['item-quick-button__description']}>{description}</p>
              <div className={styles['item-quick-button__icon']}>
                <Icon />
              </div>
            </button>
          </div>
        );
      })}
    </div>
  );
}

const QUICK_BUTTONS_ANALYTICS_LABEL = 'Dashboard page';

type TQuickButton = {
  title: string;
  description: string;
  analyticsEventName: string;
  analyticsCategory: EAnalyticsCategory;
  analyticsLabel: string;
  Icon(props: React.SVGAttributes<SVGElement>): JSX.Element;
  action(): void;
};

const trackClickQuickButton = ({ analyticsEventName, analyticsCategory, analyticsLabel }: TQuickButton) => {
  analytics.send(analyticsEventName, {
    category: analyticsCategory,
    label: analyticsLabel,
    action: EAnalyticsAction.Initiated,
  });
};
