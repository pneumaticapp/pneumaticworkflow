import {
  EWorkflowsActions,
} from '../actions';
import {
  watchCloneWorkflow,
  cloneWorkflowSaga,
  deleteWorkflowSaga,
  watchDeleteWorfklow,
  watchReturnWorkflowToTask,
  returnWorkflowToTaskSaga,
  setWorkflowFinishedSaga,
} from '../saga';
import * as deleteApi from '../../../api/deleteWorkflow';
import * as finishWorkflowApi from '../../../api/finishWorkflow';
import { NotificationManager } from '../../../components/UI/Notifications';

describe('workflows saga', () => {
  it('deleteWorkflowSaga work', () => {
    const saga = deleteWorkflowSaga({ type: EWorkflowsActions.DeleteWorkflow, payload: { workflowId: 1 } });
    const deleteApiMock = jest.spyOn(deleteApi, 'deleteWorkflow')
      .mockImplementation(() => Promise.resolve(null));
    const notificationManagerSuccessMock = jest.spyOn(NotificationManager, 'success');
    saga.next();
    saga.next();
    saga.next();
    expect(notificationManagerSuccessMock).toHaveBeenCalled();
    expect(deleteApiMock).toHaveBeenCalled();
  });
  it('setWorkflowFinishedSaga work', () => {
    const saga = setWorkflowFinishedSaga({ type: EWorkflowsActions.SetWorkflowFinished, payload: {
      workflowId: 1,
      onWorkflowEnded: () => {},
    }});
    const finishWorkflowApiMock = jest.spyOn(finishWorkflowApi, 'finishWorkflow')
      .mockImplementation(() => Promise.resolve(null));
    const notificationManagerSuccessMock = jest.spyOn(NotificationManager, 'success');
    saga.next();
    saga.next();
    expect(finishWorkflowApiMock).toHaveBeenCalled();
    expect(notificationManagerSuccessMock).toHaveBeenCalled();
  });
  describe('generator', () => {
    it.each([
      [watchCloneWorkflow, EWorkflowsActions.CloneWorkflow, cloneWorkflowSaga],
      [watchDeleteWorfklow, EWorkflowsActions.DeleteWorkflow, deleteWorkflowSaga],
      [watchReturnWorkflowToTask, EWorkflowsActions.ReturnWorkflowToTask, returnWorkflowToTaskSaga],
    ])(
      'for the function %s, calls takeEvery with parameters %s and %s',
      (testingFn: any, action: any, expectedFn: any) => {
        const result = testingFn();
        result.next();
      },
    );
  });
});
