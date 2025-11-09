export type CitizenPayload = {
  email: string;
  first_name: string;
  last_name?: string;
  phone: string;
  city_id: number;
  password: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type CitizenResponse = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  city: {
    id: number;
    name: string;
    state: {
      id: number;
      name: string;
      abbreviation: string;
    };
  };
};

export type AuthTokens = {
  access: string;
  refresh: string;
};

export type AuthUser = {
  id?: number;
  email: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  cityName?: string;
  stateAbbreviation?: string;
};
