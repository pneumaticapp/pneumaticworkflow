const LOWERCASE = 'abcdefghijklmnopqrstuvwxyz';
const UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const DIGITS = '0123456789';
const SPECIAL = '!@#$%^&*';
const ALL_CHARACTERS = LOWERCASE + UPPERCASE + DIGITS + SPECIAL;

const getRandomChar = (chars: string): string => chars[Math.floor(Math.random() * chars.length)];

const shuffleString = (str: string): string => {
  const arr = str.split('');

  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }

  return arr.join('');
};

export const createPassword = (length = 8): string => {
  const password = [
    getRandomChar(LOWERCASE),
    getRandomChar(UPPERCASE),
    getRandomChar(DIGITS),
    getRandomChar(SPECIAL),
  ];

  for (let i = password.length; i < length; i += 1) {
    password.push(getRandomChar(ALL_CHARACTERS));
  }

  return shuffleString(password.join(''));
};
