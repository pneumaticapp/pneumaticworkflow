import type { EventChannel } from 'redux-saga';
import { call, take } from 'redux-saga/effects';

import { createWebSocketChannel } from '../utils/createWebSocketChannel';
import { parseCookies } from '../../utils/cookie';
import { envWssURL } from '../../constants/enviroment';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mergePaths } from '../../utils/urls';
import type { IRealtimeWsEnvelope } from './types';
import { routeRealtimeEvent } from './utils/routeRealtimeEvent';



export function* watchWsEvents() {
  const { api: { wsPublicUrl, urls } } = getBrowserConfigEnv();
  const url = mergePaths(
    envWssURL || wsPublicUrl,
    `${urls.wsEvents}?auth_token=${parseCookies(document.cookie).token}`,
  );

  const channel: EventChannel<IRealtimeWsEnvelope> = yield call(createWebSocketChannel, url);

  while (true) {
    const envelope: IRealtimeWsEnvelope = yield take(channel);
    yield call(routeRealtimeEvent, envelope);
  }
}
