figures = config["tree"]["figures"]
fignum = 1
for figure_name in figures:

    figscript = figures[figure_name]["script"]
    graphics = figures[figure_name]["graphics"]
    datasets = figures[figure_name]["datasets"]
    dependencies = figures[figure_name]["dependencies"]
    command = figures[figure_name]["command"]

    if command is None:
        continue

    if figscript is None:
        figscript = []

    rulename = f"fig{fignum}"
    fignum += 1

    rule:
        """
        Generate a figure given a figure script and optional dependencies.

        """
        name:
            rulename
        input:
            figscript,
            datasets,
            dependencies,
            "environment.yml",
        output:
            report(graphics, category="Figure")
        conda:
            (paths.user / "environment.yml").as_posix()
        params:
            command=command
        script:
            "../scripts/figure.py"