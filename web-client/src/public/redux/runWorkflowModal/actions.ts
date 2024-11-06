import { ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { IRunWorkflow } from '../../components/WorkflowEditPopup/types';

export const enum ERunWorkflowModalActions {
  OpenModal = 'OPEN_RUN_WORKFLOW_MODAL',
  CloseModal = 'CLOSE_RUN_WORKFLOW_MODAL',
  RunWorkflow = 'RUN_WORKFLOW',
  RunWorkflowSuccess = 'RUN_WORKFLOW_SUCCESS',
  RunWorkflowFailed = 'RUN_WORKFLOW_FAILED',
}

export type TOpenRunWorkflowModal = ITypedReduxAction<ERunWorkflowModalActions.OpenModal, IRunWorkflow>;
export const openRunWorkflowModal: (payload: IRunWorkflow) => TOpenRunWorkflowModal =
  actionGenerator<ERunWorkflowModalActions.OpenModal, IRunWorkflow>(ERunWorkflowModalActions.OpenModal);

export type TCloseRunWorkflowModal = ITypedReduxAction<ERunWorkflowModalActions.CloseModal, void>;
export const closeRunWorkflowModal: (payload?: void) => TCloseRunWorkflowModal =
  actionGenerator<ERunWorkflowModalActions.CloseModal, void>(ERunWorkflowModalActions.CloseModal);

export type TRunWorkflow = ITypedReduxAction<ERunWorkflowModalActions.RunWorkflow, IRunWorkflow>;
export const runWorkflow: (payload: IRunWorkflow) => TRunWorkflow =
  actionGenerator<ERunWorkflowModalActions.RunWorkflow, IRunWorkflow>(ERunWorkflowModalActions.RunWorkflow);

export type TRunWorkflowSuccess = ITypedReduxAction<ERunWorkflowModalActions.RunWorkflowSuccess, void>;
export const runWorkflowSuccess: (payload?: void) => TRunWorkflowSuccess =
  actionGenerator<ERunWorkflowModalActions.RunWorkflowSuccess, void>(ERunWorkflowModalActions.RunWorkflowSuccess);

export type TRunWorkflowFailed = ITypedReduxAction<ERunWorkflowModalActions.RunWorkflowFailed, void>;
export const runWorkflowFailed: (payload?: void) => TRunWorkflowFailed =
  actionGenerator<ERunWorkflowModalActions.RunWorkflowFailed, void>(ERunWorkflowModalActions.RunWorkflowFailed);

export type TRunWorkflowModalActions = TOpenRunWorkflowModal
| TCloseRunWorkflowModal
| TRunWorkflow
| TRunWorkflowSuccess
| TRunWorkflowFailed;
