const AVATAR_SIZE = 20;
const AVATAR_OVERLAP = 4;

export const getPerformersAvatarsWidth = (performerCount: number): number => {
  if (performerCount <= 0) {
    return AVATAR_SIZE;
  }

  return AVATAR_SIZE + (performerCount - 1) * (AVATAR_SIZE - AVATAR_OVERLAP);
};
