import { connect } from 'react-redux';

import { ITemplateControllsProps, TemplateControlls } from './TemplateControlls';
import {
  patchTemplate,
  cloneTemplate,
  deleteTemplate,
  openRunWorkflowModal,
} from '../../../redux/actions';

type TDispatchProps = Pick<
  ITemplateControllsProps,
  'patchTemplate' | 'cloneTemplate' | 'deleteTemplate' | 'openRunWorkflowModal'
>;

export const mapDispatchToProps: TDispatchProps = {
  patchTemplate,
  cloneTemplate,
  deleteTemplate,
  openRunWorkflowModal,
};

export const TemplateControllsContainer = connect<{}, TDispatchProps>(null, mapDispatchToProps)(TemplateControlls);
