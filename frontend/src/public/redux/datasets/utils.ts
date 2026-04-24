import { CLONE_WORD, CLONE_SUFFIX_REGEX, ESCAPE_REGEX } from './constants';

export function getCloneBaseName(name: string): string {
  return name.replace(CLONE_SUFFIX_REGEX, '');
}

export function generateCloneName(baseName: string, existingNames: string[]): string {
  let maxNumber = 0;
  const regex = buildCloneNumberRegex(baseName);

  existingNames.forEach((name) => {
    const match = name.match(regex);
    if (match) {
      maxNumber = Math.max(maxNumber, parseInt(match[1], 10));
    }
  });

  return `${baseName} (${CLONE_WORD} ${maxNumber + 1})`;
}

function buildCloneNumberRegex(baseName: string): RegExp {
  return new RegExp(`^${sanitizeForRegex(baseName)}\\s+\\(${CLONE_WORD}\\s+(\\d+)\\)$`);
}

function sanitizeForRegex(str: string): string {
  return str.replace(ESCAPE_REGEX, '\\$&');
}