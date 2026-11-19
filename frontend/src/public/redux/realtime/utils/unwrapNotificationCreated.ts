import type { TRealtimeWsEnvelope, TWsNotificationCreatedData } from '../types';
import { ERealtimeEnvelopeType, isNotificationDataType } from '../types';
import type { TNotificationMappingEnvelope } from './mapNotificationFromWs';

export function isNotificationCreatedEnvelope(envelope: TRealtimeWsEnvelope): envelope is TRealtimeWsEnvelope & {
  type: ERealtimeEnvelopeType.NOTIFICATION_CREATED;
  data: TWsNotificationCreatedData;
} {
  return envelope.type === ERealtimeEnvelopeType.NOTIFICATION_CREATED;
}

export function unwrapNotificationCreatedEnvelope(
  envelope: TRealtimeWsEnvelope & {
    type: ERealtimeEnvelopeType.NOTIFICATION_CREATED;
    data: TWsNotificationCreatedData;
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
