import { mapTemplateFieldsetsToRuntime } from '../mapTemplateFieldsetsToRuntime';
import { makeFieldsetBinding } from '../../__stubs__/fieldsets.factory';
import { makeTemplateResponse } from '../../__stubs__/templates.factory';

describe('mapTemplateFieldsetsToRuntime', () => {
  it('returns empty fieldsets when kickoff has no fieldsets', () => {
    const template = makeTemplateResponse();
    const { normalizedTemplate, loadedFieldsets } = mapTemplateFieldsetsToRuntime(template);

    expect(loadedFieldsets).toEqual([]);
    expect(normalizedTemplate.kickoff.fieldsets).toEqual([]);
  });

  it('returns normalizedTemplate with apiNameBinding in kickoff fieldsets', () => {
    const template = makeTemplateResponse({
      kickoff: {
        description: '',
        fields: [],
        fieldsets: [makeFieldsetBinding({ apiName: 'bind-abc', sharedFieldsetId: 42, name: 'Contacts' })],
      },
    });

    const { normalizedTemplate } = mapTemplateFieldsetsToRuntime(template);

    expect(normalizedTemplate.kickoff.fieldsets).toHaveLength(1);
    expect(normalizedTemplate.kickoff.fieldsets[0].apiNameBinding).toBe('bind-abc');
    expect(normalizedTemplate.kickoff.fieldsets[0]).not.toHaveProperty('apiName');
    expect(normalizedTemplate.kickoff.fieldsets[0].sharedFieldsetId).toBe(42);
  });

  it('returns loadedFieldsets as IFieldsetRuntime with apiNameBinding', () => {
    const template = makeTemplateResponse({
      kickoff: {
        description: '',
        fields: [],
        fieldsets: [makeFieldsetBinding({ apiName: 'bind-xyz', name: 'Addresses' })],
      },
    });

    const { loadedFieldsets } = mapTemplateFieldsetsToRuntime(template);

    expect(loadedFieldsets).toHaveLength(1);
    expect(loadedFieldsets[0].apiNameBinding).toBe('bind-xyz');
    expect(loadedFieldsets[0].name).toBe('Addresses');
    expect(loadedFieldsets[0]).not.toHaveProperty('apiName');
    expect(loadedFieldsets[0]).not.toHaveProperty('sharedFieldsetId');
  });

  it('preserves other template properties unchanged', () => {
    const template = makeTemplateResponse({
      kickoff: { description: '', fields: [], fieldsets: [makeFieldsetBinding()] },
    });
    const { normalizedTemplate } = mapTemplateFieldsetsToRuntime(template);

    expect(normalizedTemplate.id).toBe(1);
    expect(normalizedTemplate.name).toBe('Template');
    expect(normalizedTemplate.kickoff.description).toBe('');
    expect(normalizedTemplate.kickoff.fields).toEqual([]);
    expect(normalizedTemplate.tasks).toEqual([]);
  });

  it('handles multiple fieldsets correctly', () => {
    const template = makeTemplateResponse({
      kickoff: {
        description: '',
        fields: [],
        fieldsets: [
          makeFieldsetBinding({ apiName: 'fs-a', name: 'A', order: 0 }),
          makeFieldsetBinding({ apiName: 'fs-b', name: 'B', order: 1 }),
        ],
      },
    });

    const { normalizedTemplate, loadedFieldsets } = mapTemplateFieldsetsToRuntime(template);

    expect(normalizedTemplate.kickoff.fieldsets).toHaveLength(2);
    expect(normalizedTemplate.kickoff.fieldsets[0].apiNameBinding).toBe('fs-a');
    expect(normalizedTemplate.kickoff.fieldsets[1].apiNameBinding).toBe('fs-b');

    expect(loadedFieldsets).toHaveLength(2);
    expect(loadedFieldsets[0].apiNameBinding).toBe('fs-a');
    expect(loadedFieldsets[1].apiNameBinding).toBe('fs-b');
  });
});
