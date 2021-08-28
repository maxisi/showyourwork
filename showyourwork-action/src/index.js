// Imports
const core = require("@actions/core");
const shell = require("shelljs");
const { formatRepo } = require("./format_repo");
const { setupConda } = require("./conda");
const { buildArticle } = require("./article");
const { generateReport } = require("./report");
const { publishOutput } = require("./publish");

(async () => {
  try {
    // Exit on failure
    shell.set("-e");

    // Format repository if it's a fresh fork
    formatRepo();

    // Setup conda or restore from cache
    await setupConda();

    // Build the article
    output = await buildArticle();

    // Generate the report
    report = await generateReport();

    // Publish the article output
    await publishOutput(output, report);
  } catch (error) {
    // Exit gracefully
    core.setFailed(error.message);
  }
})();