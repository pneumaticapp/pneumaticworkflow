/* eslint-disable */
/* prettier-ignore */
import { ContentState, EntityInstance } from 'draft-js';

interface IFoundEntity {
  entityKey: string;
  blockKey: string;
  entity: EntityInstance;
  offset: number;
  length: number;
  index: number;
  lastIndex: number;
}

export const getEntitiesByLogic = (
  content: ContentState,
  findEntity: (entity: EntityInstance) => boolean,
  blockKey?: string,
) => {
  const entities = [] as IFoundEntity[];
  let blockOffset = 0;

  content.getBlocksAsArray().forEach(block => {
    if (blockKey && blockKey !== block.getKey()) {
      blockOffset += block.getLength() + 1;

      return;
    }

    let selectedEntity: Pick<IFoundEntity, 'entityKey' | 'blockKey' | 'entity'> | null = null;

    block.findEntityRanges(character => {
      if (character.getEntity() === null) {
        return false;
      }

      const entityKey = character.getEntity();
      const entity = content.getEntity(entityKey);

      // If our logic is successful
      if (findEntity(entity)) {
        // set data
        selectedEntity = {
          entityKey,
          blockKey: block.getKey(),
          entity: content.getEntity(character.getEntity()),
        };

        return true;
      }

      return false;
    },
    (start, end) => {
      // We are using this function because in most of the scenarios when using entity,
      // we need start and end position of the entity as well which we only get here
      if (!selectedEntity) {
        return;
      }

      entities.push({
        ...selectedEntity,
        offset: start + blockOffset,
        length: end - start,
        index: start,
        lastIndex: end,
      });
    },
    );

    blockOffset += block.getLength() + 1;
  });

  return entities;
};
