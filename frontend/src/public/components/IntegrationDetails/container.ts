/* prettier-ignore */
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { loadIntegrationDetails } from '../../redux/actions';
import type { IApplicationState } from '../../redux/store';
import { IIntegrationDetailsProps, IntegrationDetails } from './IntegrationDetails';

type TIntegrationDetailsStoreProps = Pick<IIntegrationDetailsProps, 'isLoading' | 'integration'>;
type TIntegrationDetailsDispatchProps = Pick<IIntegrationDetailsProps, 'loadIntegrationDetails'>;

function mapStateToProps({ integrations: { detailed } }: IApplicationState): TIntegrationDetailsStoreProps {
  return {
    isLoading: detailed.isLoading,
    integration: detailed.data,
  };
}

const mapDispatchToProps: TIntegrationDetailsDispatchProps = { loadIntegrationDetails };

export const IntegrationDetailsContainer = withRouter(connect(mapStateToProps, mapDispatchToProps)(IntegrationDetails));
