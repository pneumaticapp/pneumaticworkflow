import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import {
  setSelectTemplateModalTemplates,
  loadSelectTemplateModalTemplates,
} from '../../redux/selectTemplateModal/actions';
import { closeSelectTemplateModal, openRunWorkflowModalSideMenu } from '../../redux/actions';

import { ISelectTemplateModalProps, SelectTemplateModal } from './SelectTemplateModal';

export type TMainLayoutComponentStoreProps = Pick<
ISelectTemplateModalProps,
| 'items'
| 'isLoading'
| 'isModalOpened'
| 'isAdmin'
| 'ancestorTaskId'
>;

export type TMainLayoutComponentDispatchProps = Pick<
ISelectTemplateModalProps,
| 'setSelectTemplateModalTemplates'
| 'openRunWorkflowModal'
| 'loadSelectTemplateModalTemplates'
| 'closeSelectTemplateModal'
>;

const mapStateToProps = ({
  selectTemplateModal: { items, isLoading, isOpen, ancestorTaskId },
  authUser: {
    isAdmin,
  },
}: IApplicationState): TMainLayoutComponentStoreProps => {
  return {
    isModalOpened: isOpen,
    isLoading,
    items,
    ancestorTaskId,
    isAdmin: Boolean(isAdmin),
  };
};

const mapDispatchToProps = {
  setSelectTemplateModalTemplates,
  openRunWorkflowModal: openRunWorkflowModalSideMenu,
  loadSelectTemplateModalTemplates,
  closeSelectTemplateModal,
};

export const SelectTemplateModalContainer = connect<TMainLayoutComponentStoreProps, TMainLayoutComponentDispatchProps>
(mapStateToProps, mapDispatchToProps)(SelectTemplateModal);
