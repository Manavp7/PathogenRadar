import { createContext, useContext } from "react";

/** Currently-selected region key (undefined = backend default). */
export const RegionContext = createContext<string | undefined>(undefined);

export const useRegion = () => useContext(RegionContext);
