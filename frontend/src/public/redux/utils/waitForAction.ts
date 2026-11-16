import { take } from 'redux-saga/effects';

export function* waitForAction(actionType: string) {
  yield take(actionType);
}
