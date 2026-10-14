const pool = require("../db/pool");

// Simulates the "cron job / Redis TTL callback" from the spec using a simple interval.
// In production this would run as a scheduled job (node-cron / BullMQ) against Redis + Postgres.
async function releaseExpiredLocks() {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const { rows: expired } = await client.query(
      `SELECT id, product_variant_id FROM price_locks WHERE status = 'active' AND expires_at < NOW() FOR UPDATE`
    );
    for (const lock of expired) {
      await client.query("UPDATE price_locks SET status = 'expired' WHERE id = $1", [lock.id]);
      await client.query(
        "UPDATE product_variants SET reserved_quantity = GREATEST(0, reserved_quantity - 1) WHERE id = $1",
        [lock.product_variant_id]
      );
    }
    await client.query("COMMIT");
    if (expired.length) console.log(`Released ${expired.length} expired price lock(s).`);
  } catch (e) {
    await client.query("ROLLBACK");
    console.error("Error releasing expired locks:", e.message);
  } finally {
    client.release();
  }
}

function startLockExpiryJob(intervalMs = 5000) {
  setInterval(releaseExpiredLocks, intervalMs);
}

module.exports = { startLockExpiryJob, releaseExpiredLocks };
