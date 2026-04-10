// <reference types="jest" />
import { generateCloneName, getCloneBaseName } from '../utils';

describe('generateCloneName', () => {
  it('appends (clone 1) when no existing clones', () => {
    const result = generateCloneName('MyDS', ['MyDS']);
    expect(result).toBe('MyDS (clone 1)');
  });

  it('picks the next number after existing clones', () => {
    const result = generateCloneName('MyDS', ['MyDS', 'MyDS (clone 1)', 'MyDS (clone 2)']);
    expect(result).toBe('MyDS (clone 3)');
  });

  it('handles special characters in the base name', () => {
    const result = generateCloneName('Test (v2)', ['Test (v2)']);
    expect(result).toBe('Test (v2) (clone 1)');
  });
});

describe('getCloneBaseName', () => {
  it('returns name as-is when there is no clone suffix', () => {
    const result = getCloneBaseName('MyDS');
    expect(result).toBe('MyDS');
  });

  it('strips the clone suffix from the name', () => {
    const result = getCloneBaseName('MyDS (clone 3)');
    expect(result).toBe('MyDS');
  });
});
