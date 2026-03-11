import { IApplicationState } from "../../types/redux";
import { TeamPages } from "../team/types";

export const getTeamPage = (state: IApplicationState): TeamPages => state.team.page;