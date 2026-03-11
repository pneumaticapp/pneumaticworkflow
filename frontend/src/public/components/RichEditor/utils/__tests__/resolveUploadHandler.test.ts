import { resolveUploadHandler } from '../resolveUploadHandler';

describe('resolveUploadHandler', () => {
  const builtIn = jest.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    builtIn.mockClear();
  });

  it('returns propHandler when provided', () => {
    const prop = jest.fn();
    expect(resolveUploadHandler(prop)).toBe(prop);
    expect(resolveUploadHandler(prop, builtIn)).toBe(prop);
  });

  it('returns builtInHandler when propHandler is undefined', () => {
    expect(resolveUploadHandler(undefined, builtIn)).toBe(builtIn);
  });

  it('returns undefined when both are undefined', () => {
    expect(resolveUploadHandler(undefined)).toBeUndefined();
    expect(resolveUploadHandler(undefined, undefined)).toBeUndefined();
  });

  it('returns undefined when propHandler is undefined and builtIn is undefined', () => {
    expect(resolveUploadHandler(undefined, undefined)).toBeUndefined();
  });
});
