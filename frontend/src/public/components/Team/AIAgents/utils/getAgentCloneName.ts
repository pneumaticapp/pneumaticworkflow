export const getAgentCloneName = (name: string, suffix: string, existingNames: string[]): string => {
  const takenNames = new Set(existingNames.map((existingName) => existingName.trim().toLowerCase()));
  const getCandidate = (index: number) => (index === 1 ? `${name} (${suffix})` : `${name} (${suffix} ${index})`);

  let index = 1;
  while (takenNames.has(getCandidate(index).toLowerCase())) {
    index += 1;
  }

  return getCandidate(index);
};
