// src/pages/api/users.ts
export interface User {
  username: string;
  email: string;
  password: string; // hashed password
  role: string;
}

export const users: User[] = [];
