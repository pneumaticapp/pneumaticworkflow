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
import { cloneWorkflowAction, deleteWorkflowAction, returnWorkflowToTaskAction, setWorkflowFinished } from '../slice';

describe('workflows saga', () => {
  it('deleteWorkflowSaga work', () => {
    const saga = deleteWorkflowSaga({ type: deleteWorkflowAction.type, payload: { workflowId: 1 } });
    const deleteApiMock = jest.spyOn(deleteApi, 'deleteWorkflow').mockImplementation(() => Promise.resolve(null));
    const notificationManagerSuccessMock = jest.spyOn(NotificationManager, 'success');
    saga.next();
    saga.next();
    saga.next();
    expect(notificationManagerSuccessMock).toHaveBeenCalled();
    expect(deleteApiMock).toHaveBeenCalled();
  });
  it('setWorkflowFinishedSaga work', () => {
    const saga = setWorkflowFinishedSaga({
      type: setWorkflowFinished.type,
      payload: {
        workflowId: 1,
        onWorkflowEnded: () => {},
      },
    });
    const finishWorkflowApiMock = jest
      .spyOn(finishWorkflowApi, 'finishWorkflow')
      .mockImplementation(() => Promise.resolve(null));
    const notificationManagerSuccessMock = jest.spyOn(NotificationManager, 'success');
    saga.next();
    saga.next();
    expect(finishWorkflowApiMock).toHaveBeenCalled();
    expect(notificationManagerSuccessMock).toHaveBeenCalled();
  });
  describe('generator', () => {
    it.each([
      [watchCloneWorkflow, cloneWorkflowAction.type, cloneWorkflowSaga],
      [watchDeleteWorfklow, deleteWorkflowAction.type, deleteWorkflowSaga],
      [watchReturnWorkflowToTask, returnWorkflowToTaskAction.type, returnWorkflowToTaskSaga],
    ])(
      'for the function %s, calls takeEvery with parameters %s and %s',
      (testingFn: any, action: any, expectedFn: any) => {
        const result = testingFn();
        result.next();
      },
    );
  });
});
