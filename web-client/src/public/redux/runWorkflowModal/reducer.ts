import { IStoreRunWorkflowModal } from '../../types/redux';
import { ERunWorkflowModalActions, TRunWorkflowModalActions } from './actions';

export const INIT_STATE: IStoreRunWorkflowModal = {
  workflow: null,
  isWorkflowStarting: false,
  isOpen: false,
};

export const reducer = (state = INIT_STATE, action: TRunWorkflowModalActions): IStoreRunWorkflowModal => {
  switch (action.type) {
    case ERunWorkflowModalActions.OpenModal:
      return { ...state, workflow: action.payload, isOpen: true };
    case ERunWorkflowModalActions.CloseModal:
      return { ...state, workflow: null, isOpen: false };
    case ERunWorkflowModalActions.RunWorkflow:
      return { ...state, isWorkflowStarting: true };
    case ERunWorkflowModalActions.RunWorkflowSuccess:
      return { ...state, isWorkflowStarting: false, isOpen: false };
    case ERunWorkflowModalActions.RunWorkflowFailed:
      return { ...state, isWorkflowStarting: false };

    default: return { ...state };
  }
};
