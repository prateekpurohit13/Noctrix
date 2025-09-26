import { NextApiRequest, NextApiResponse } from "next";
import bcrypt from "bcryptjs";
import { users } from "@/lib/store";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  const { username, email, password, role } = req.body;

  if (!username || !email || !password || !role) {
    return res.status(400).json({ error: "All fields are required" });
  }

  const existingUser = users.find(u => u.username === username || u.email === email);
  if (existingUser) return res.status(400).json({ error: "User already exists" });

  const hashedPassword = await bcrypt.hash(password, 10);
  users.push({ username, email, password: hashedPassword, role });

  res.status(200).json({ message: "User registered successfully" });
}
