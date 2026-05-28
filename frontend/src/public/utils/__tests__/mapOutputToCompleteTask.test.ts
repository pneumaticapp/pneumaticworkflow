import { mapOutputToCompleteTask } from '../mappers';
import { EExtraFieldType, IExtraField } from '../../types/template';

jest.mock('../dateTime', () => ({
  getEndOfDayTsp: jest.fn((v: string) => `endOfDay(${v})`),
  toDateString: jest.fn(),
  toTspDate: jest.fn(),
  toISOStringFromTsp: jest.fn(),
  formatDateToISOInWorkflow: jest.fn(),
  formatDateToISOInTask: jest.fn(),
}));

const makeField = (overrides: Partial<IExtraField>): IExtraField => ({
  apiName: 'field-1',
  name: 'Test',
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
  ...overrides,
});

describe('mapOutputToCompleteTask', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns empty array as-is', () => {
    expect(mapOutputToCompleteTask([])).toEqual([]);
  });

  describe('checkbox normalization', () => {
    it('splits a single-option string into array', () => {
      const output = [makeField({ type: EExtraFieldType.Checkbox, value: 'New option' })];
      const [first] = mapOutputToCompleteTask(output);
      expect(first.value).toEqual(['New option']);
    });

    it('splits a multi-option comma-separated string into array', () => {
      const output = [makeField({ type: EExtraFieldType.Checkbox, value: 'opt1, opt2, opt3' })];
      const [first] = mapOutputToCompleteTask(output);
      expect(first.value).toEqual(['opt1', 'opt2', 'opt3']);
    });

    it('keeps array value as-is', () => {
      const output = [makeField({ type: EExtraFieldType.Checkbox, value: ['opt1', 'opt2'] })];
      const [first] = mapOutputToCompleteTask(output);
      expect(first.value).toEqual(['opt1', 'opt2']);
    });

    it.each([null, undefined, ''])('returns empty array for falsy value: %p', (falsy) => {
      const output = [makeField({ type: EExtraFieldType.Checkbox, value: falsy as any })];
      const [first] = mapOutputToCompleteTask(output);
      expect(first.value).toEqual([]);
    });

    it('keeps empty array as empty array', () => {
      const output = [makeField({ type: EExtraFieldType.Checkbox, value: [] })];
      const [first] = mapOutputToCompleteTask(output);
      expect(first.value).toEqual([]);
    });

    it('preserves other field properties', () => {
      const output = [makeField({
        apiName: 'cb-field',
        name: 'My Checkbox',
        type: EExtraFieldType.Checkbox,
        value: 'opt',
        isRequired: true,
      })];
      const [first] = mapOutputToCompleteTask(output);
      expect(first).toEqual(expect.objectContaining({
        apiName: 'cb-field',
        name: 'My Checkbox',
        type: 'checkbox',
        value: ['opt'],
        isRequired: true,
      }));
    });
  });

  it('handles mixed field types in one output array', () => {
    const output = [
      makeField({ apiName: 'cb', type: EExtraFieldType.Checkbox, value: 'opt1, opt2' }),
      makeField({ apiName: 'num', type: EExtraFieldType.Number, value: '1,5' }),
      makeField({ apiName: 'txt', type: EExtraFieldType.Text, value: 'hi' }),
    ];
    const result = mapOutputToCompleteTask(output);
    expect(result).toEqual([
      expect.objectContaining({ apiName: 'cb', value: ['opt1', 'opt2'] }),
      expect.objectContaining({ apiName: 'num', value: '1.5' }),
      expect.objectContaining({ apiName: 'txt', value: 'hi' }),
    ]);
  });
});
