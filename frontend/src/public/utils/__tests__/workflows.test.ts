import { getEditKickoff } from '../workflows';
import { makeExtraField } from '../../__stubs__/fields.factory';
import { makeFieldsetRuntime } from '../../__stubs__/fieldsets.factory';
import { IWorkflowDetailsKickoff } from '../../types/workflow';

describe('getEditKickoff', () => {
  it('returns fieldsets as an empty array even when the source kickoff has fieldsets', () => {
    const workflowKickoff: IWorkflowDetailsKickoff = {
      id: 1,
      description: 'Kickoff description',
      output: [makeExtraField({ apiName: 'f1', value: 'v1' })],
      fieldsets: [makeFieldsetRuntime({ apiNameBinding: 'fs-1' })],
    };

    const result = getEditKickoff(workflowKickoff);

    expect(result.fieldsets).toEqual([]);
    expect(result.description).toBe('Kickoff description');
    expect(result.fields).toEqual(
      expect.arrayContaining([expect.objectContaining({ apiName: 'f1' })]),
    );
  });

  it('returns empty string description when source description is null', () => {
    const workflowKickoff: IWorkflowDetailsKickoff = {
      id: 1,
      description: null,
      output: [],
    };

    const result = getEditKickoff(workflowKickoff);

    expect(result.description).toBe('');
    expect(result.fieldsets).toEqual([]);
    expect(result.fields).toEqual([]);
  });
});
