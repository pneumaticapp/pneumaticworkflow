import * as React from 'react';
import { useSelector } from 'react-redux';

import { UserData } from '../UserData/container';
import { IUserDataWithGroupProps } from './types';
import { IApplicationState } from '../../types/redux';
import { ETaskPerformerType, ETemplateOwnerType } from '../../types/template';

const UserDataWithGroup: React.FC<IUserDataWithGroupProps> = ({ type, idItem, children }) => {
  const groups = useSelector((state: IApplicationState) => state.groups.list);
  const aiAgents = useSelector((state: IApplicationState) => state.aiAgents.list);

  if (type === ETemplateOwnerType.UserGroup) {
    const currentGroup = groups.find(({ id }) => id === idItem);
    if (!currentGroup) return null;
    const groupAvatar = {
      type: ETemplateOwnerType.UserGroup,
      firstName: currentGroup.name,
    };

    return <>{children(groupAvatar)}</>;
  }

  if (type === ETaskPerformerType.AiAgent) {
    const currentAgent = aiAgents.find(({ id }) => id === idItem);
    if (!currentAgent) return null;
    const agentAvatar = {
      id: currentAgent.id,
      type: ETaskPerformerType.AiAgent,
      firstName: currentAgent.name,
      photo: currentAgent.photo,
    };

    return <>{children(agentAvatar)}</>;
  }


  return (
    <UserData userId={idItem}>
      {(user) => {
        if (!user) return null;

        return <>{children(user)}</>;
      }}
    </UserData>
  );
};

export default UserDataWithGroup;
