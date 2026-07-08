import { EIntegrations } from '../../../../types/integrations';

import { checkShowDraftTemplateWarning } from '../checkShowDraftTemplateWarning';
import { hasTemplateIntegrations } from '../templateIntegrations';

describe('templateIntegrations', () => {
  describe('hasTemplateIntegrations', () => {
    it('returns false when template has no integrations', () => {
      expect(hasTemplateIntegrations(false, [])).toBe(false);
    });

    it('returns true when template is public', () => {
      expect(hasTemplateIntegrations(true, [])).toBe(true);
    });

    it('returns true when template has connected integrations', () => {
      expect(hasTemplateIntegrations(false, [EIntegrations.API])).toBe(true);
    });
  });
});

describe('checkShowDraftTemplateWarning', () => {
  it('returns false for active template', () => {
    expect(checkShowDraftTemplateWarning(true, true, [EIntegrations.API])).toBe(false);
  });

  it('returns false for inactive template without integrations', () => {
    expect(checkShowDraftTemplateWarning(false, false, [])).toBe(false);
  });

  it('returns true for inactive public template', () => {
    expect(checkShowDraftTemplateWarning(false, true, [])).toBe(true);
  });

  it('returns true for inactive template with integrations', () => {
    expect(checkShowDraftTemplateWarning(false, false, [EIntegrations.Zapier])).toBe(true);
  });

  it('returns false for inactive template with only webhooks', () => {
    expect(checkShowDraftTemplateWarning(false, false, [])).toBe(false);
  });
});
