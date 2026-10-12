import { EExtraFieldType } from '../../types/template';
import { EWorkflowStatus, TWorkflowDetailsKickoffResponse } from '../../types/workflow';
import { makeExtraField } from '../../__stubs__/fields.factory';
import { makeFieldsetTaskAPI } from '../../__stubs__/fieldsets.factory';
import { makeWorkflowResponse } from '../../__stubs__/workflows.factory';
import { mapBackendKickoffToRedux, mapBackendKickoffToRuntime, mapBackendWorkflowToRedux } from '../mappers';

const mapKickoff = (kickoff: TWorkflowDetailsKickoffResponse) => {
  const result = mapBackendKickoffToRedux(kickoff, 'UTC');
  if (result == null) throw new Error('mapBackendKickoffToRedux returned null for non-null kickoff');

  return result;
};

describe('mapBackendKickoffToRedux', () => {
  it('returns null when kickoff is null', () => {
    expect(mapBackendKickoffToRedux(null, 'UTC')).toBeNull();
  });

  it('converts IFieldsetTaskAPI to IFieldsetRuntime (apiName to apiNameBinding)', () => {
    const result = mapKickoff({
      id: 1,
      description: '',
      output: [],
      fieldsets: [makeFieldsetTaskAPI({ id: 10, apiName: 'fs-abc' })],
    });

    expect(result.fieldsets).toHaveLength(1);
    expect(result.fieldsets[0].apiNameBinding).toBe('fs-abc');
    expect('id' in result.fieldsets[0]).toBe(false);
  });

  it('formats timestamp to string for Date fields in output', () => {
    const result = mapKickoff({
      id: 2,
      description: '',
      output: [
        makeExtraField({
          type: EExtraFieldType.Date,
          value: 1718409600,
        }),
      ],
      fieldsets: [],
    });

    expect(result.output[0].value).toMatch(/15, 2024/);
  });

  it('formats timestamp to string for Date fields in fieldsets', () => {
    const result = mapKickoff({
      id: 3,
      description: '',
      output: [],
      fieldsets: [
        makeFieldsetTaskAPI({
          fields: [
            makeExtraField({
              type: EExtraFieldType.Date,
              value: 1718409600,
            }),
          ],
        }),
      ],
    });

    expect(result.fieldsets[0].fields[0].value).toMatch(/15, 2024/);
  });

  it('keeps values unchanged for non-Date fields', () => {
    const result = mapKickoff({
      id: 4,
      description: '',
      output: [
        makeExtraField({
          type: EExtraFieldType.String,
          value: 'keep-me',
        }),
      ],
      fieldsets: [],
    });

    expect(result.output[0].value).toBe('keep-me');
  });

  it('preserves kickoff id and description', () => {
    const result = mapKickoff({
      id: 42,
      description: 'test description',
      output: [],
      fieldsets: [],
    });

    expect(result.id).toBe(42);
    expect(result.description).toBe('test description');
  });

  it('handles multiple fieldsets', () => {
    const result = mapKickoff({
      id: 5,
      description: '',
      output: [],
      fieldsets: [makeFieldsetTaskAPI({ id: 1, apiName: 'first' }), makeFieldsetTaskAPI({ id: 2, apiName: 'second' })],
    });

    expect(result.fieldsets).toHaveLength(2);
    expect(result.fieldsets[0].apiNameBinding).toBe('first');
    expect(result.fieldsets[1].apiNameBinding).toBe('second');
  });
});

describe('mapBackendWorkflowToRedux', () => {
  it('maps kickoff and preserves remaining workflow fields', () => {
    const mockWorkflow = makeWorkflowResponse({
      id: 100,
      name: 'Test Workflow',
      owners: [1, 2],
      dueDateTsp: 1718409600,
      kickoff: {
        id: 1,
        description: 'Workflow kickoff',
        output: [],
        fieldsets: [makeFieldsetTaskAPI({ id: 10, apiName: 'fs-workflow' })],
      },
    });

    const result = mapBackendWorkflowToRedux(mockWorkflow, 'UTC');

    expect(result.id).toBe(100);
    expect(result.name).toBe('Test Workflow');
    expect(result.status).toBe(EWorkflowStatus.Running);
    expect(result.owners).toEqual([1, 2]);
    expect(result.dueDateTsp).toBe(1718409600);
    expect(result.kickoff.id).toBe(1);
    expect(result.kickoff.description).toBe('Workflow kickoff');
    expect(result.kickoff.fieldsets[0].apiNameBinding).toBe('fs-workflow');
    expect('id' in result.kickoff.fieldsets[0]).toBe(false);
  });

  it('throws an error when kickoff is missing', () => {
    const mockWorkflowWithoutKickoff = makeWorkflowResponse({
      kickoff: null as unknown as TWorkflowDetailsKickoffResponse,
    });

    expect(() => {
      mapBackendWorkflowToRedux(mockWorkflowWithoutKickoff, 'UTC');
    }).toThrow('kickoff is required in workflow details');
  });
});

describe('mapBackendKickoffToRuntime', () => {
  it('returns null when kickoff is null', () => {
    expect(mapBackendKickoffToRuntime(null)).toBeNull();
  });

  it('maps fieldsets (apiName to apiNameBinding, removes id)', () => {
    const result = mapBackendKickoffToRuntime({
      id: 1,
      description: 'test',
      output: [],
      fieldsets: [makeFieldsetTaskAPI({ id: 10, apiName: 'fs-runtime' })],
    });

    expect(result).not.toBeNull();
    expect(result!.fieldsets[0].apiNameBinding).toBe('fs-runtime');
    expect('id' in result!.fieldsets[0]).toBe(false);
  });

  it('keeps raw timestamp values for date fields without string formatting', () => {
    const rawTimestamp = 1725134400;
    const result = mapBackendKickoffToRuntime({
      id: 2,
      description: '',
      output: [
        makeExtraField({
          type: EExtraFieldType.Date,
          value: rawTimestamp,
        }),
      ],
      fieldsets: [
        makeFieldsetTaskAPI({
          fields: [
            makeExtraField({
              type: EExtraFieldType.Date,
              value: rawTimestamp,
            }),
          ],
        }),
      ],
    });

    expect(result).not.toBeNull();
    expect(result!.output[0].value).toBe(rawTimestamp);
    expect(result!.fieldsets[0].fields[0].value).toBe(rawTimestamp);
  });
});
