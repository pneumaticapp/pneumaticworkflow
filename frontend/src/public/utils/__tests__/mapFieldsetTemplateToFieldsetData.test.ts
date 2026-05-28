
import { mapFieldsetTemplateToFieldsetData } from '../mapFieldsetTemplateToFieldsetData';

const makeFieldsetTemplate = (overrides = {}) => ({
  id: 1,
  apiName: 'fs-test',
  name: 'Test Fieldset',
  description: 'A test fieldset',
  order: 0,
  labelPosition: 'top',
  rules: [],
  fields: [],
  ...overrides,
});

const makeField = (overrides = {}) => ({
  apiName: 'field-1',
  name: 'Field One',
  description: 'Desc',
  type: 'string',
  isRequired: false,
  isHidden: false,
  order: 0,
  default: '',
  selections: [],
  dataset: null,
  ...overrides,
});

describe('mapFieldsetTemplateToFieldsetData', () => {
  describe('camelCase keys (happy path)', () => {
    it('correctly maps all fields from camelCase format', () => {
      const template = makeFieldsetTemplate({
        fields: [makeField({ apiName: 'f-1', name: 'Name', type: 'text', isRequired: true, isHidden: false, order: 3, default: 'hello' })],
        rules: [{ id: 1, type: 'show', value: 'x' }],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.id).toBe(1);
      expect(result.apiName).toBe('fs-test');
      expect(result.name).toBe('Test Fieldset');
      expect(result.description).toBe('A test fieldset');
      expect(result.order).toBe(0);
      expect(result.labelPosition).toBe('top');
      expect(result.rulesCount).toBe(1);

      expect(result.fields).toHaveLength(1);
      expect(result.fields[0]).toEqual(expect.objectContaining({
        apiName: 'f-1',
        name: 'Name',
        type: 'text',
        isRequired: true,
        isHidden: false,
        order: 3,
        value: 'hello',
      }));
    });
  });

  describe('snake_case keys (fallback)', () => {
    it('uses snake_case keys when camelCase are absent', () => {
      const template = {
        id: 2,
        api_name: 'fs-snake',
        name: 'Snake',
        description: '',
        order: 1,
        label_position: 'left',
        rules: [],
        fields: [{
          api_name: 'f-snake',
          name: 'Snake Field',
          type: 'number',
          is_required: true,
          is_hidden: true,
          order: 5,
        }],
      };

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.apiName).toBe('fs-snake');
      expect(result.labelPosition).toBe('left');
      expect(result.fields[0].apiName).toBe('f-snake');
      expect(result.fields[0].isRequired).toBe(true);
      expect(result.fields[0].isHidden).toBe(true);
    });
  });

  describe('camelCase priority over snake_case', () => {
    it('picks camelCase when both keys are present', () => {
      const template = makeFieldsetTemplate({
        apiName: 'camel-wins',
        api_name: 'snake-loses',
        labelPosition: 'left',
        label_position: 'top',
        fields: [{
          apiName: 'camel-field',
          api_name: 'snake-field',
          name: 'F',
          type: 'string',
          isRequired: true,
          is_required: false,
          isHidden: true,
          is_hidden: false,
          order: 0,
        }],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.apiName).toBe('camel-wins');
      expect(result.labelPosition).toBe('left');
      expect(result.fields[0].apiName).toBe('camel-field');
      expect(result.fields[0].isRequired).toBe(true);
      expect(result.fields[0].isHidden).toBe(true);
    });
  });

  describe('edge cases', () => {
    it('returns empty fields when fields property is absent', () => {
      const template = makeFieldsetTemplate({ fields: undefined });
      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.fields).toEqual([]);
    });

    it('uses fallback apiName = fieldset-{id} when apiName is empty', () => {
      const template = makeFieldsetTemplate({ apiName: '', api_name: '', id: 42 });
      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.apiName).toBe('fieldset-42');
    });

    it('uses index as fallback for field order', () => {
      const template = makeFieldsetTemplate({
        fields: [
          makeField({ apiName: 'first', order: undefined }),
          makeField({ apiName: 'second', order: undefined }),
        ],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.fields[0].order).toBe(0);
      expect(result.fields[1].order).toBe(1);
    });
  });

  describe('default to value mapping', () => {
    it('copies f.default into field value', () => {
      const template = makeFieldsetTemplate({
        fields: [makeField({ default: 'prefilled' })],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.fields[0].value).toBe('prefilled');
    });

    it('sets empty string when default is not provided', () => {
      const template = makeFieldsetTemplate({
        fields: [makeField({ default: undefined })],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.fields[0].value).toBe('');
    });
  });

  describe('labelPosition normalization', () => {
    it.each([
      ['left', 'left'],
      ['top', 'top'],
      [undefined, 'top'],
      ['garbage', 'top'],
    ] as const)('labelPosition = %s results in %s', (input, expected) => {
      const template = makeFieldsetTemplate({
        labelPosition: input,
        label_position: undefined,
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.labelPosition).toBe(expected);
    });
  });

  describe('rulesCount', () => {
    it('counts rules from the array', () => {
      const template = makeFieldsetTemplate({
        rules: [{ id: 1 }, { id: 2 }, { id: 3 }],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.rulesCount).toBe(3);
    });

    it('returns 0 when rules is absent', () => {
      const template = makeFieldsetTemplate({ rules: undefined });
      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.rulesCount).toBe(0);
    });

    it('returns 0 when rules is not an array', () => {
      const template = makeFieldsetTemplate({ rules: 'invalid' });
      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.rulesCount).toBe(0);
    });
  });

  describe('selections and dataset', () => {
    it('passes selections and dataset from field without modifications', () => {
      const selections = [{ apiName: 'opt-1', value: 'Option 1' }];
      const template = makeFieldsetTemplate({
        fields: [makeField({ selections, dataset: 5 })],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.fields[0].selections).toBe(selections);
      expect(result.fields[0].dataset).toBe(5);
    });
  });
});
