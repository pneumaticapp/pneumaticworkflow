import type { IWorkflowLogItem } from '../../../types/workflow';
import type { IRealtimeWsEnvelope } from '../types';
import { ERealtimeEnvelopeType } from '../types';

export function mapWsEnvelopeToWorkflowLogItem(envelope: IRealtimeWsEnvelope): IWorkflowLogItem | null {
  if (
    envelope.type === ERealtimeEnvelopeType.EVENT_CREATED ||
    envelope.type === ERealtimeEnvelopeType.EVENT_UPDATED
  ) {
    return envelope.data;
  }

  return null;
}
