<?php
$secret = getenv('NETNOVA_INSTALL_SECRET') ?: 'change-me-now';
$message = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $provided = $_POST['secret'] ?? '';

    if (!hash_equals($secret, $provided)) {
        $message = 'Invalid secret key.';
    } else {
        $cmd = 'bash scripts/website_install.sh 2>&1';
        $output = shell_exec($cmd);
        $message = "Installer executed. Output:\n" . ($output ?: '[no output]');
    }
}
?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NET NOVA ISP BILLING One-Click Installer</title>
    <style>
      body { font-family: Arial, sans-serif; max-width: 900px; margin: 2rem auto; line-height: 1.5; }
      .card { border: 1px solid #ccc; border-radius: 8px; padding: 1rem; }
      input, button { padding: .6rem; margin-top: .5rem; width: 100%; }
      pre { white-space: pre-wrap; background: #111; color: #0f0; padding: 1rem; border-radius: 8px; }
    </style>
  </head>
  <body>
    <h1>NET NOVA ISP BILLING Installer</h1>
    <p>Open this page on your server and run installation. For safety, set <code>NETNOVA_INSTALL_SECRET</code> in your web server environment first.</p>
    <div class="card">
      <form method="post">
        <label>Installer Secret</label>
        <input type="password" name="secret" required />
        <button type="submit">Install NET NOVA ISP BILLING</button>
      </form>
    </div>
    <?php if ($message): ?>
      <h3>Result</h3>
      <pre><?= htmlspecialchars($message) ?></pre>
    <?php endif; ?>
  </body>
</html>
