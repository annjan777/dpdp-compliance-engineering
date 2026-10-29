import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export async function signup(input: { email: string; phone: string; name: string; aadhaarNumber: string }) {
  // Aadhaar is collected "for verification" but nothing reads it after signup
  return prisma.user.create({ data: { ...input } });
}

export async function marketingList() {
  return prisma.user.findMany({ where: { marketingOptIn: true }, select: { email: true } });
}
