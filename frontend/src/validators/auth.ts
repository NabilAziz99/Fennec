import { z } from 'zod';

const email = z.string().email('Please enter a valid email address.');

const password = z
  .string()
  .min(6, 'Password must be at least 8 characters long.');

export const loginSchema = z.object({
  email,
  password,
});

export const signupSchema = z.object({
  email,
  password,
});

export type LoginInput = z.infer<typeof loginSchema>;
export type SignupInput = z.infer<typeof signupSchema>;
