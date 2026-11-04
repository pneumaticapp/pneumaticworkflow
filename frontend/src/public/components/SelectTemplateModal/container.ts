import { connect } from 'react-redux';

import type { RootState } from '../../redux/store';
import {
  setSelectTemplateModalTemplates,
  loadSelectTemplateModalTemplates,
} from '../../redux/selectTemplateModal/actions';
import { closeSelectTemplateModal, openRunWorkflowModalSideMenu } from '../../redux/actions';

import { ISelectTemplateModalProps, SelectTemplateModal } from './SelectTemplateModal';

export type TMainLayoutComponentStoreProps = Pick<
  ISelectTemplateModalProps,
  'items' | 'isLoading' | 'isModalOpened' | 'isAdmin' | 'ancestorTaskId'
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
  authUser: { isAdmin },
}: RootState): TMainLayoutComponentStoreProps => {
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

export const SelectTemplateModalContainer = connect<TMainLayoutComponentStoreProps, TMainLayoutComponentDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SelectTemplateModal);
