/* eslint-disable react/destructuring-assignment */
import * as React from 'react';
import { IntlShape } from 'react-intl';

import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import { resendVerification } from '../../api/resendVerification';
import { TopNavContainer } from '../../components/TopNav';
import { VerificationReminder } from '../../components/VerificationReminder';
import { EDashboardTimeRange } from '../../types/dashboard';
import { EDashboardModes } from '../../types/redux';
import { SelectMenu, Tabs } from '../../components/UI';
import { FilterIcon } from '../../components/icons';

import styles from './DashboardLayout.css';

export interface IDashboardLayoutStoreProps {
  isAccountOwner: boolean;
  isVerified?: boolean;
  currentTimeRange: EDashboardTimeRange;
  dashboardMode: EDashboardModes;
  isAdmin?: boolean;
}

export interface IDashboardLayoutDispatchProps {
  resendVerification(): void;
  setTimeRange(payload: EDashboardTimeRange): void;
  setDashboardMode(payload: EDashboardModes): void;
  setDashboardSettingsManuallyChanged(): void;
}

export interface IDashboardLayoutState {
  isResendClicked: boolean;
}

type TAppLayoutComponentProps = IDashboardLayoutStoreProps &
  IDashboardLayoutDispatchProps & {
    intl: IntlShape;
  };

const timeRangesTitles = Object.values(EDashboardTimeRange);

export class DashboardLayoutComponent extends React.Component<TAppLayoutComponentProps> {
  private dashboardModes = Object.values(EDashboardModes).map((mode) => ({
    id: mode,
    label: this.props.intl.formatMessage({ id: mode }),
  }));

  public state = {
    isResendClicked: false,
  };

  public renderDashboardContent = () => {
    const { currentTimeRange, dashboardMode, setTimeRange, setDashboardMode, setDashboardSettingsManuallyChanged } =
      this.props;

    const handleSetTimeRange = (newTimeRange: EDashboardTimeRange) => {
      setDashboardSettingsManuallyChanged();
      setTimeRange(newTimeRange);
    };

    const handleSetDashboardMode = (newDashboardMode: EDashboardModes) => {
      setDashboardMode(newDashboardMode);
    };

    return (
      <div className={styles['navbar-left__content']}>
        <div className={styles['filters']}>
          {this.props.isAdmin && (
            <Tabs values={this.dashboardModes} activeValueId={dashboardMode} onChange={handleSetDashboardMode} />
          )}
          <SelectMenu
            values={timeRangesTitles}
            activeValue={currentTimeRange}
            onChange={handleSetTimeRange}
            Icon={FilterIcon}
          />
        </div>
      </div>
    );
  };

  private handleResendVerification = async () => {
    this.setState({ isResendClicked: true });
    try {
      await resendVerification();
      NotificationManager.success({ message: 'dashboard.resend-verification' });
    } catch (e) {
      logger.error(e);
      NotificationManager.warning({ message: getErrorMessage(e) });
      this.setState({ isResendClicked: false });
    }
  };

  private renderVerificationRiminder = () => {
    const { isVerified, isAccountOwner } = this.props;
    const { isResendClicked } = this.state;

    if (isVerified || !isAccountOwner) {
      return null;
    }

    return (
      <VerificationReminder isResendClicked={isResendClicked} resendVerification={this.handleResendVerification} />
    );
  };

  public render() {
    const leftContent = this.renderDashboardContent();

    return (
      <>
        <TopNavContainer leftContent={leftContent} centerContent={this.renderVerificationRiminder()} />
        <main className={styles['main']}>
          <div className="container-fluid">{this.props.children}</div>
        </main>
      </>
    );
  }
}
