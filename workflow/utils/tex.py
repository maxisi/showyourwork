from . import paths, exceptions
import subprocess
import shutil


__all__ = ["compile_tex"]


def compile_tex(config, args=[], stylesheet=None):
    """
    Compile the TeX document using `tectonic`.

    """
    # Copy over TeX auxiliaries
    for file in config["tex_files_in"]:
        src = paths.user / file
        dst = paths.tex / src.name
        if not dst.exists():
            shutil.copy(str(src), str(dst))

    # Copy over the actual stylesheet
    if stylesheet is not None:
        shutil.copy(str(stylesheet), str(paths.tex / ".showyourwork.tex"))

    # Run tectonic
    result = subprocess.run(
        ["tectonic"] + args + [paths.user / config["ms_tex"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        # TODO: Log these
        # TODO: Keep all logs
        print(result.stdout.decode("utf-8"))
        print(result.stderr.decode("utf-8"))
        # TODO
        raise exceptions.TectonicError()