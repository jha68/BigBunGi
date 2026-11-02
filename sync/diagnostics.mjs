export function safeDiagnostic(value, secrets = []) {
  let text = String(value || "").replace(/\u001b\[[0-?]*[ -/]*[@-~]/g, "");
  for (const secret of [...secrets]
    .filter(Boolean)
    .sort((a, b) => b.length - a.length))
    text = text.split(secret).join("[REDACTED]");
  return text.replace(
    /pbkdf2-100000:[a-f0-9]{32}:[a-f0-9]{64}/g,
    "[REDACTED HASH]",
  );
}

export function errorAnnotation(message, secrets) {
  const safe = safeDiagnostic(message, secrets)
    .slice(0, 2000)
    .replace(/%/g, "%25")
    .replace(/\r/g, "%0D")
    .replace(/\n/g, "%0A");
  return `::error title=Cloudflare sync deployment::${safe}`;
}

export function commandFailure(command, stdout, stderr) {
  const text = safeDiagnostic(`${stderr || ""}\n${stdout || ""}`).trim();
  const error = text.match(/(?:ERROR|Error:|error:)[\s\S]*/)?.[0];
  return `Cloudflare ${command} failed: ${error || text || "command exited unsuccessfully"}`;
}
