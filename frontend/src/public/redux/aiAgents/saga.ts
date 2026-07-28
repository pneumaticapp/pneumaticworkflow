import { all, fork, takeEvery, put } from 'redux-saga/effects';

import { logger } from '../../utils/logger';
import { getAiAgents } from '../../api/aiAgents/getAiAgents';
import { IAiAgent } from './types';

import { loadAiAgents, loadAiAgentsSuccess, loadAiAgentsFailed } from './slice';

function* loadAiAgentsSaga() {
  try {
    const agents: IAiAgent[] = yield getAiAgents();

    yield put(loadAiAgentsSuccess(agents));
  } catch (error) {
    // 403 means AI performers are not enabled for the account
    yield put(loadAiAgentsFailed());
    if (error?.status !== 403) {
      logger.error('failed to load AI agents', error);
    }
  }
}

export function* watchLoadAiAgents() {
  yield takeEvery(loadAiAgents.type, loadAiAgentsSaga);
}

export function* rootSaga() {
  yield all([fork(watchLoadAiAgents)]);
}
