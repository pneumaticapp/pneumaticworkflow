import type { IRealtimeWsEnvelope, IWsNotificationCreatedData } from '../types';
import { ERealtimeEnvelopeType, isNotificationDataType } from '../types';
import type { TNotificationMappingEnvelope } from './mapNotificationFromWs';

export function isNotificationCreatedEnvelope(
  envelope: IRealtimeWsEnvelope,
): envelope is IRealtimeWsEnvelope & {
  type: ERealtimeEnvelopeType.NOTIFICATION_CREATED;
  data: IWsNotificationCreatedData;
} {
  return envelope.type === ERealtimeEnvelopeType.NOTIFICATION_CREATED;
}

export function unwrapNotificationCreatedEnvelope(
  envelope: IRealtimeWsEnvelope & {
    type: ERealtimeEnvelopeType.NOTIFICATION_CREATED;
    data: IWsNotificationCreatedData;
  },
): TNotificationMappingEnvelope | null {
  const { data } = envelope;

  if (!isNotificationDataType(data.type)) {
    return null;
  }

  return {
    type: data.type,
    data,
  } as TNotificationMappingEnvelope;
}
