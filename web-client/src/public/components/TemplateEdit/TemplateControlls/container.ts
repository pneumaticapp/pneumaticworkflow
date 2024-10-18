import { connect } from 'react-redux';

import { IApplicationState } from '../../../types/redux';

import { ITemplateControllsProps, TemplateControlls } from './TemplateControlls';
import { 
  patchTemplate,
  cloneTemplate,
  deleteTemplate,
  openRunWorkflowModal,
} from '../../../redux/actions';
import { getIsUserSubsribed } from '../../../redux/selectors/user';

type TStoreProps = Pick<ITemplateControllsProps, 'template' | 'templateStatus' | 'isSubscribed'>;
type TDispatchProps = Pick<ITemplateControllsProps, 'patchTemplate' | 'cloneTemplate' | 'deleteTemplate' | 'openRunWorkflowModal'>;

export function mapStateToProps(state: IApplicationState): TStoreProps {
  const {
    template: { data: template, status },
  } = state;

  const isSubscribed = getIsUserSubsribed(state);

  return { template, templateStatus: status, isSubscribed };
}

export const mapDispatchToProps: TDispatchProps = {
  patchTemplate,
  cloneTemplate,
  deleteTemplate,
  openRunWorkflowModal,
};

export const TemplateControllsContainer = connect(mapStateToProps, mapDispatchToProps)(TemplateControlls);
