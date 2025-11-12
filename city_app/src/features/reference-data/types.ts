export type State = {
  id: number;
  name: string;
  abbreviation: string;
};

export type City = {
  id: number;
  name: string;
  state: State;
};

export type Department = {
  id: number;
  name: string;
  email: string;
  phone: string;
  description: string;
};

export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string;
  department: Department;
};

export type Tag = {
  id: number;
  name: string;
  slug: string;
};
