import { IAccountPlan, IApplicationState } from "../../types/redux";

export const getAccountPlan = (state: IApplicationState): IAccountPlan => state.accounts.planInfo;
