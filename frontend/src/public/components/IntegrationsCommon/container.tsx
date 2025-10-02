/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { loadApiKey } from '../../redux/actions';
import { IApplicationState } from '../../types/redux';
import { IntegrationsCommon, IIntegrationsCommonProps } from './IntegrationsCommon';

type TIntegrationsCommonStoreProps = Pick<IIntegrationsCommonProps, 'apiKey' | 'isApiKeyLoading'>;
type TIntegrationsCommonDispatchProps = Pick<IIntegrationsCommonProps, 'loadApiKey'>;

function mapStateToProps({ integrations: { apiKey } }: IApplicationState): TIntegrationsCommonStoreProps {

  return {
    apiKey: apiKey.data,
    isApiKeyLoading: apiKey.isLoading,
  };
}

const mapDispatchToProps: TIntegrationsCommonDispatchProps = { loadApiKey };

export const IntegrationsCommonContainer = connect(mapStateToProps, mapDispatchToProps)(IntegrationsCommon);
