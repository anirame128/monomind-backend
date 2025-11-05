-- Step 0: Enable pgcrypto extension for gen_random_uuid and gen_random_bytes
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Step 1: Create projects table
CREATE TABLE "projects" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "api_key" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "projects_pkey" PRIMARY KEY ("id")
);

-- Step 2: Add usage tracking to users
ALTER TABLE "users" ADD COLUMN "tier" TEXT NOT NULL DEFAULT 'FREE';
ALTER TABLE "users" ADD COLUMN "api_requests_used" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "users" ADD COLUMN "usage_reset_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Step 3: Create default project for existing users
INSERT INTO "projects" ("id", "user_id", "name", "description", "api_key", "created_at", "updated_at")
SELECT 
    gen_random_uuid()::text,
    "clerk_user_id",
    'My First Project',
    'Default project created during migration',
    'mk_proj_' || replace(encode(gen_random_bytes(32), 'base64'), '/', '_'),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM "users";

-- Step 4: Add project_id to repositories (nullable first)
ALTER TABLE "repositories" ADD COLUMN "project_id" TEXT;

-- Step 5: Assign all existing repositories to their user's default project
UPDATE "repositories" r
SET "project_id" = (
    SELECT p."id" 
    FROM "projects" p 
    WHERE p."user_id" = r."user_id" 
    LIMIT 1
);

-- Step 6: Make project_id NOT NULL
ALTER TABLE "repositories" ALTER COLUMN "project_id" SET NOT NULL;

-- Step 7: Drop old foreign keys first
ALTER TABLE "repositories" DROP CONSTRAINT IF EXISTS "repositories_user_id_fkey";
ALTER TABLE "api_keys" DROP CONSTRAINT IF EXISTS "api_keys_user_id_fkey";

-- Step 8: Add new foreign key constraints
ALTER TABLE "projects" ADD CONSTRAINT "projects_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("clerk_user_id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "repositories" ADD CONSTRAINT "repositories_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- Step 9: Drop old indexes
DROP INDEX IF EXISTS "repositories_github_id_key";
DROP INDEX IF EXISTS "repositories_user_id_github_id_key";
DROP INDEX IF EXISTS "repositories_user_id_status_idx";

-- Step 10: Drop old api_keys table
DROP TABLE IF EXISTS "api_keys";

-- Step 11: Update repository constraints
ALTER TABLE "repositories" ADD CONSTRAINT "repositories_project_id_github_id_key" UNIQUE ("project_id", "github_id");

-- Step 12: Create new indexes
CREATE UNIQUE INDEX "projects_api_key_key" ON "projects"("api_key");
CREATE INDEX "projects_user_id_idx" ON "projects"("user_id");
CREATE INDEX "projects_api_key_idx" ON "projects"("api_key");
CREATE INDEX "repositories_project_id_status_idx" ON "repositories"("project_id", "status");
CREATE INDEX "repositories_user_id_idx" ON "repositories"("user_id");
