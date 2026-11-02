// Local integration tests only; this password is never used by deploy.mjs.
import { Miniflare } from "miniflare";
import { readFile } from "node:fs/promises";
import { pbkdf2Sync } from "node:crypto";
const password = "test-only-sync-password";
const salt = "abcdef1234567890abcdef1234567890";
const mf = new Miniflare({
  modules: true,
  scriptPath: new URL("./worker.js", import.meta.url).pathname,
  compatibilityDate: "2026-07-01",
  host: "127.0.0.1",
  port: Number(process.env.SYNC_TEST_PORT || 4301),
  cf: false,
  d1Databases: ["DB"],
  bindings: {
    APP_ORIGIN: "https://bigbungi.junununseo.com",
    PASSWORD_HASH: `pbkdf2-100000:${salt}:${pbkdf2Sync(password, Buffer.from(salt, "hex"), 100000, 32, "sha256").toString("hex")}`,
  },
});
const db = await mf.getD1Database("DB");
await db.exec(await readFile(new URL("./schema.sql", import.meta.url), "utf8"));
console.log("Local sync integration server:", String(await mf.ready));
for (const signal of ["SIGTERM", "SIGINT"])
  process.on(signal, async () => {
    await mf.dispose();
    process.exit(0);
  });
