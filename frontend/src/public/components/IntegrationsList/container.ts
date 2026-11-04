import { connect } from 'react-redux';
import { loadIntegrationsList } from '../../redux/actions';
import type { IApplicationState } from '../../redux/store';
import { IIntegrationsListProps, IntegrationsList } from './IntegrationsList';

type TIntegrationsListStoreProps = Pick<IIntegrationsListProps, 'isLoading' | 'integrations'>;
type TIntegrationsListDispatchProps = Pick<IIntegrationsListProps, 'loadIntegrationsList'>;

function mapStateToProps({ integrations: { list } }: IApplicationState): TIntegrationsListStoreProps {
  return {
    isLoading: list.isLoading,
    integrations: list.data,
  };
}

const mapDispatchToProps: TIntegrationsListDispatchProps = { loadIntegrationsList };

export const IntegrationsListContainer = connect(mapStateToProps, mapDispatchToProps)(IntegrationsList);
