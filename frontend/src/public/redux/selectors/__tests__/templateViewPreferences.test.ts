import { selectExtraFieldLabelsBesideForTemplate } from '../templateViewPreferences';
import { ELocale, IApplicationState } from '../../../types/redux';

const buildState = (map: Record<number, boolean>): IApplicationState =>
  ({
    template: { extraFieldLabelsBesideByTemplateId: map },
    settings: { locale: ELocale.English },
  }) as IApplicationState;

describe('selectExtraFieldLabelsBesideForTemplate', () => {
  it('returns false when templateId is undefined', () => {
    expect(selectExtraFieldLabelsBesideForTemplate(buildState({}), undefined)).toBe(false);
  });

  it('returns false when template has no stored preference (default stacked)', () => {
    expect(selectExtraFieldLabelsBesideForTemplate(buildState({}), 42)).toBe(false);
  });

  it('returns true when template is stored as beside', () => {
    expect(selectExtraFieldLabelsBesideForTemplate(buildState({ 42: true }), 42)).toBe(true);
  });

  it('returns false for legacy false entry (stacked)', () => {
    expect(selectExtraFieldLabelsBesideForTemplate(buildState({ 42: false }), 42)).toBe(false);
  });
});
