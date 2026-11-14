import { connect } from 'react-redux';

import type { RootState } from '../../../redux/store';

import type { ITemplateControllsProps } from './TemplateControlls';
import { TemplateControlls } from './TemplateControlls';
import { patchTemplate, cloneTemplate, deleteTemplate, openRunWorkflowModal } from '../../../redux/actions';
import { getIsUserSubsribed } from '../../../redux/selectors/user';

type TStoreProps = Pick<ITemplateControllsProps, 'template' | 'templateStatus' | 'isSubscribed'>;
type TDispatchProps = Pick<
  ITemplateControllsProps,
  'patchTemplate' | 'cloneTemplate' | 'deleteTemplate' | 'openRunWorkflowModal'
>;

export function mapStateToProps(state: RootState): TStoreProps {
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
