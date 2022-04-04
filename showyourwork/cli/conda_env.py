from .. import __version__
from .. import paths
from .. import exceptions
from ..logging import get_logger
import subprocess
import shutil
import yaml
import filecmp
import jinja2
from pathlib import Path
import re


def run(command, **kwargs):
    """Run a command in the isolated showyourwork conda environment."""

    # Logging
    logger = get_logger()

    # Command to set up conda
    try:
        conda_prefix = subprocess.check_output("conda info --base", shell=True)
    except subprocess.CalledProcessError:
        # TODO
        raise exceptions.ShowyourworkException()
    conda_prefix = conda_prefix.decode().replace("\n", "")
    conda_setup = f". {conda_prefix}/etc/profile.d/conda.sh"

    # Various conda environment files
    syw_envfile = paths.showyourwork().module / "environment.yml"
    workflow_envfile = paths.user().temp / "environment.yml"
    cached_envfile = paths.user().home_temp / "environment.yml"

    # Infer the `showyourwork` version from the user's config file
    user_config = yaml.load(
        jinja2.Environment(loader=jinja2.FileSystemLoader(paths.user().repo))
        .get_template("showyourwork.yml")
        .render(),
        Loader=yaml.CLoader,
    )
    syw_spec = user_config.get("showyourwork", {}).get("version", "any")
    if syw_spec == "any":
        # No specific version provided
        syw_spec = "showyourwork"
    elif syw_spec == "latest":
        # Latest version from GitHub
        syw_spec = "git+https://github.com/showyourwork/showyourwork.git@main#egg=showyourwork"
    elif re.match("(?:(\d+\.[.\d]*\d+))", syw_spec):
        # This is an actual package version
        syw_spec = f"showyourwork=={syw_spec}"
    elif re.match("[0-9a-f]{5,40}", syw_spec):
        # This is a commit SHA
        syw_spec = f"git+https://github.com/showyourwork/showyourwork.git@{syw_spec}#egg=showyourwork"
    else:
        # Assume it's a local path to the package
        if not Path(syw_spec).is_absolute():
            syw_spec = (paths.user().repo / syw_spec).resolve()
        syw_spec = f"-e {syw_spec}"

    # Copy the showyourwork environment file to a temp location,
    # and add the user's requested showyourwork version as a dependency
    # so we can import it within Snakemake
    with open(syw_envfile, "r") as f:
        syw_env = yaml.load(f, Loader=yaml.CLoader)
    for dep in syw_env["dependencies"]:
        if type(dep) is dict and "pip" in dep:
            dep["pip"].append(syw_spec)
    with open(workflow_envfile, "w") as f:
        print(yaml.dump(syw_env, Dumper=yaml.CDumper), file=f)

    # Set up or update our isolated conda env
    if not paths.user().env.exists():
        # Set up a new env and cache the envfile
        logger.info(
            "Creating a new conda environment in ~/.showyourwork/env..."
        )
        subprocess.run(
            f"conda env create -p {paths.user().env} -f {workflow_envfile} -q",
            shell=True,
        )
        shutil.copy(workflow_envfile, cached_envfile)
    else:
        # We'll update the env based on our spec file if the current
        # environment differs (based on checking the cached spec file)
        if cached_envfile.exists():
            cache_hit = filecmp.cmp(
                cached_envfile, workflow_envfile, shallow=False
            )
        else:
            cache_hit = False

        if not cache_hit:
            logger.info("Updating conda environment in ~/.showyourwork/env...")
            subprocess.run(
                f"conda env update -p {paths.user().env} -f {workflow_envfile} --prune -q",
                shell=True,
            )
            shutil.copy(workflow_envfile, cached_envfile)

    # Command to activate our environment
    conda_activate = f"{conda_setup} && conda activate {paths.user().env}"

    # Run
    return subprocess.run(
        f"{conda_activate} && {command}",
        shell=True,
        **kwargs,
    )