import { getAnimationTaskHeight } from '../TemplateAIModal';

describe('getAnimationTaskHeight', () => {
  it('returns null when rawHeight is undefined (offsetHeight null-safety, Sentry S6)', () => {
    expect(getAnimationTaskHeight(undefined, 0)).toBeNull();
    expect(getAnimationTaskHeight(undefined, 1)).toBeNull();
  });

  it('returns null when rawHeight is null', () => {
    expect(getAnimationTaskHeight(null, 0)).toBeNull();
  });

  it('returns rawHeight + 0 for order 0', () => {
    expect(getAnimationTaskHeight(100, 0)).toBe(100);
  });

  it('returns rawHeight + 8 for order > 0', () => {
    expect(getAnimationTaskHeight(100, 1)).toBe(108);
  });
});
