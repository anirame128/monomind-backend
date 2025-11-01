/*
  Warnings:

  - A unique constraint covering the columns `[github_id]` on the table `users` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "users" ADD COLUMN     "github_access_token" TEXT,
ADD COLUMN     "github_id" INTEGER,
ADD COLUMN     "github_username" TEXT,
ADD COLUMN     "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- CreateTable
CREATE TABLE "repositories" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "github_id" INTEGER NOT NULL,
    "github_url" TEXT NOT NULL,
    "full_name" TEXT NOT NULL,
    "default_branch" TEXT NOT NULL DEFAULT 'main',
    "is_private" BOOLEAN NOT NULL DEFAULT false,
    "webhook_id" INTEGER,
    "webhook_secret" TEXT,
    "display_name" TEXT,
    "description" TEXT,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "indexed_at" TIMESTAMP(3),
    "last_synced_at" TIMESTAMP(3),
    "last_commit_sha" TEXT,
    "error_message" TEXT,
    "file_count" INTEGER NOT NULL DEFAULT 0,
    "total_size" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "repositories_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "repositories_github_id_key" ON "repositories"("github_id");

-- CreateIndex
CREATE INDEX "repositories_user_id_status_idx" ON "repositories"("user_id", "status");

-- CreateIndex
CREATE INDEX "repositories_webhook_id_idx" ON "repositories"("webhook_id");

-- CreateIndex
CREATE UNIQUE INDEX "repositories_user_id_github_id_key" ON "repositories"("user_id", "github_id");

-- CreateIndex
CREATE UNIQUE INDEX "users_github_id_key" ON "users"("github_id");

-- CreateIndex
CREATE INDEX "users_email_idx" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_github_id_idx" ON "users"("github_id");

-- AddForeignKey
ALTER TABLE "repositories" ADD CONSTRAINT "repositories_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("clerk_user_id") ON DELETE CASCADE ON UPDATE CASCADE;
