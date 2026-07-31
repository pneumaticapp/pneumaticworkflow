import { mapFieldsetBindingsToClient, mapFieldsetTaskAPIToRuntime } from '../mapFieldsetsAPIToClient';
import { EFieldLabelPosition } from '../../types/fieldset';
import { makeFieldsetField, makeFieldsetBinding, makeFieldsetTaskAPI, makeFieldsetTemplateRule } from '../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../__stubs__/fields.factory';

describe('mapFieldsetBindingsToClient', () => {
  it('returns an empty array for empty input', () => {
    expect(mapFieldsetBindingsToClient([])).toEqual([]);
  });

  it('renames apiName to apiNameBinding and drops apiName', () => {
    const result = mapFieldsetBindingsToClient([makeFieldsetBinding({ apiName: 'catalog-abc' })]);

    expect(result).toHaveLength(1);
    expect(result[0].apiNameBinding).toBe('catalog-abc');
    expect(result[0]).not.toHaveProperty('apiName');
  });

  it('preserves all other properties', () => {
    const fields = [makeFieldsetField({ apiName: 'f-1', name: 'Field 1' })];
    const binding = makeFieldsetBinding({
      apiName: 'my-fs',
      sharedFieldsetId: 42,
      name: 'My Fieldset',
      description: 'desc',
      labelPosition: EFieldLabelPosition.Left,
      layout: 'horizontal',
      order: 5,
      title: 'Title',
      rules: [makeFieldsetTemplateRule({ apiName: 'r-1', value: '100', fields: [] })],
      fields,
    });

    const [result] = mapFieldsetBindingsToClient([binding]);

    expect(result.apiNameBinding).toBe('my-fs');
    expect(result.sharedFieldsetId).toBe(42);
    expect(result.name).toBe('My Fieldset');
    expect(result.description).toBe('desc');
    expect(result.labelPosition).toBe(EFieldLabelPosition.Left);
    expect(result.layout).toBe('horizontal');
    expect(result.order).toBe(5);
    expect(result.title).toBe('Title');
    expect(result.rules).toHaveLength(1);
    expect(result.fields).toHaveLength(1);
  });

  it('maps multiple bindings', () => {
    const bindings = [
      makeFieldsetBinding({ apiName: 'fs-a' }),
      makeFieldsetBinding({ apiName: 'fs-b' }),
    ];

    const results = mapFieldsetBindingsToClient(bindings);

    expect(results).toHaveLength(2);
    expect(results[0].apiNameBinding).toBe('fs-a');
    expect(results[1].apiNameBinding).toBe('fs-b');
  });
});

describe('mapFieldsetTaskAPIToRuntime', () => {
  it('returns an empty array for empty input', () => {
    expect(mapFieldsetTaskAPIToRuntime([])).toEqual([]);
  });

  it('renames apiName to apiNameBinding and drops both id and apiName', () => {
    const result = mapFieldsetTaskAPIToRuntime([
      makeFieldsetTaskAPI({ id: 999, apiName: 'task-xyz' }),
    ]);

    expect(result).toHaveLength(1);
    expect(result[0].apiNameBinding).toBe('task-xyz');
    expect(result[0]).not.toHaveProperty('id');
    expect(result[0]).not.toHaveProperty('apiName');
  });

  it('preserves all other properties', () => {
    const fields = [makeExtraField({ apiName: 'ef-1', name: 'Extra' })];
    const taskFs = makeFieldsetTaskAPI({
      id: 50,
      apiName: 'bound-fs',
      name: 'Task FS',
      description: 'task desc',
      order: 3,
      labelPosition: EFieldLabelPosition.Left,
      layout: 'horizontal',
      title: 'Task Title',
      fields,
    });

    const [result] = mapFieldsetTaskAPIToRuntime([taskFs]);

    expect(result.apiNameBinding).toBe('bound-fs');
    expect(result.name).toBe('Task FS');
    expect(result.description).toBe('task desc');
    expect(result.order).toBe(3);
    expect(result.labelPosition).toBe(EFieldLabelPosition.Left);
    expect(result.layout).toBe('horizontal');
    expect(result.title).toBe('Task Title');
    expect(result.fields).toHaveLength(1);
  });

  it('maps multiple task fieldsets', () => {
    const fieldsets = [
      makeFieldsetTaskAPI({ id: 1, apiName: 'fs-a' }),
      makeFieldsetTaskAPI({ id: 2, apiName: 'fs-b' }),
    ];

    const results = mapFieldsetTaskAPIToRuntime(fieldsets);

    expect(results).toHaveLength(2);
    expect(results[0].apiNameBinding).toBe('fs-a');
    expect(results[1].apiNameBinding).toBe('fs-b');
  });
});
