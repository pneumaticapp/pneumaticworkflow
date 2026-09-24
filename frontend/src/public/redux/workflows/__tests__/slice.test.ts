import workflowsReducer, { clearWorkflow, openWorkflowLogPopup } from '../slice';

describe('workflows reducer', () => {
  it('closes the workflow modal when clearing workflow data', () => {
    const openState = workflowsReducer(undefined, openWorkflowLogPopup({ workflowId: 42 }));

    const clearedState = workflowsReducer(openState, clearWorkflow());

    expect(clearedState.workflow).toBeNull();
    expect(clearedState.workflowLog.isOpen).toBe(false);
    expect(clearedState.workflowLog.workflowId).toBeNull();
  });
});
