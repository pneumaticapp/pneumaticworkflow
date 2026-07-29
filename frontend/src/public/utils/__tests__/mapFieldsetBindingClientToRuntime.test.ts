import { mapFieldsToExtraFields, mapFieldsetBindingClientToRuntime } from '../mapFieldsetBindingClientToRuntime';
import { makeFieldsetField, makeFieldsetBindingClient } from '../../__stubs__/fieldsets.factory';
import { EFieldLabelPosition } from '../../types/fieldset';
import { EExtraFieldType } from '../../types/template';

describe('mapFieldsToExtraFields', () => {
  it('returns an empty array when given an empty array', () => {
    expect(mapFieldsToExtraFields([])).toEqual([]);
  });

  it('maps all IFieldsetField properties to IExtraField', () => {
    const field = makeFieldsetField({
      apiName: 'contact-email',
      name: 'Email',
      description: 'User email',
      type: 'string',
      isRequired: true,
      isHidden: false,
      order: 3,
      default: 'test@example.com',
      selections: [{ apiName: 'sel-1', value: 'Option A' }],
      dataset: 42,
    });

    const [result] = mapFieldsToExtraFields([field]);

    expect(result).toEqual({
      apiName: 'contact-email',
      name: 'Email',
      description: 'User email',
      type: 'string',
      isRequired: true,
      isHidden: false,
      order: 3,
      value: 'test@example.com',
      selections: [{ apiName: 'sel-1', value: 'Option A' }],
      dataset: 42,
      userId: null,
      groupId: null,
    });
  });

  it('applies default values for missing or falsy properties', () => {
    const field = makeFieldsetField({
      apiName: '',
      name: '',
      description: undefined,
      type: '',
      isRequired: undefined,
      isHidden: undefined,
      order: undefined,
      default: undefined,
      selections: undefined,
      dataset: undefined,
    });

    const [result] = mapFieldsToExtraFields([field]);

    expect(result.apiName).toBe('');
    expect(result.name).toBe('');
    expect(result.description).toBe('');
    expect(result.type).toBe(EExtraFieldType.String);
    expect(result.isRequired).toBe(false);
    expect(result.isHidden).toBe(false);
    expect(result.value).toBe('');
    expect(result.selections).toEqual([]);
    expect(result.dataset).toBeNull();
    expect(result.userId).toBeNull();
    expect(result.groupId).toBeNull();
  });

  it('uses index as order when order is undefined', () => {
    const fields = [
      makeFieldsetField({ apiName: 'a', order: undefined }),
      makeFieldsetField({ apiName: 'b', order: undefined }),
    ];

    const results = mapFieldsToExtraFields(fields);

    expect(results[0].order).toBe(0);
    expect(results[1].order).toBe(1);
  });

  it('preserves explicit order=0 without replacing with index', () => {
    const field = makeFieldsetField({ order: 0 });
    const [result] = mapFieldsToExtraFields([field]);
    expect(result.order).toBe(0);
  });
});

describe('mapFieldsetBindingClientToRuntime', () => {
  it('maps a binding client to runtime with converted fields', () => {
    const binding = makeFieldsetBindingClient({
      apiNameBinding: 'fs-contacts',
      name: 'Contacts',
      description: 'Contact info',
      order: 2,
      labelPosition: EFieldLabelPosition.Top,
      layout: 'horizontal',
      title: 'Contact Details',
      fields: [makeFieldsetField({ apiName: 'email', name: 'Email', type: 'string' })],
    });

    const result = mapFieldsetBindingClientToRuntime(binding);

    expect(result.apiNameBinding).toBe('fs-contacts');
    expect(result.name).toBe('Contacts');
    expect(result.description).toBe('Contact info');
    expect(result.order).toBe(2);
    expect(result.labelPosition).toBe(EFieldLabelPosition.Top);
    expect(result.layout).toBe('horizontal');
    expect(result.title).toBe('Contact Details');
    expect(result.fields).toHaveLength(1);
    expect(result.fields[0].apiName).toBe('email');
    expect(result.fields[0].type).toBe(EExtraFieldType.String);
  });

  it('normalizes labelPosition=Left to EFieldLabelPosition.Left', () => {
    const binding = makeFieldsetBindingClient({ labelPosition: EFieldLabelPosition.Left });
    const result = mapFieldsetBindingClientToRuntime(binding);
    expect(result.labelPosition).toBe(EFieldLabelPosition.Left);
  });

  it('normalizes any non-Left labelPosition to EFieldLabelPosition.Top', () => {
    const binding = makeFieldsetBindingClient({ labelPosition: EFieldLabelPosition.Top });
    const result = mapFieldsetBindingClientToRuntime(binding);
    expect(result.labelPosition).toBe(EFieldLabelPosition.Top);
  });

  it('defaults order to 0 when undefined', () => {
    const binding = makeFieldsetBindingClient({ order: undefined });
    const result = mapFieldsetBindingClientToRuntime(binding);
    expect(result.order).toBe(0);
  });

  it('defaults name and description to empty string when falsy', () => {
    const binding = makeFieldsetBindingClient({ name: '', description: '' });
    const result = mapFieldsetBindingClientToRuntime(binding);
    expect(result.name).toBe('');
    expect(result.description).toBe('');
  });

  it('handles empty fields array', () => {
    const binding = makeFieldsetBindingClient({ fields: [] });
    const result = mapFieldsetBindingClientToRuntime(binding);
    expect(result.fields).toEqual([]);
  });
});
