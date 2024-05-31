"""Script that creates a batch of randomized exams."""
from pathlib import Path

import click

from randex.exam import ExamBatch, Pool, Tex
from randex.schema import validate


@click.command(
    context_settings={"help_option_names": ["--help"]},
)
@click.argument(
    "paths",
    type=Path,
    nargs=-1,
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=1,
    help="Batch size",
)
@click.option(
    "--questions-per-folder",
    "-n",
    type=int,
    default=[1],
    multiple=True,
    help="Number of questions per folder",
)
@click.option(
    "--tex-path",
    "-t",
    type=click.Path(
        exists=True,
        resolve_path=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
    ),
    help="Path to the yaml file that contains the exam configuration",
)
@click.option(
    "--out-folder",
    "-o",
    type=Path,
    default="batch-exams",
    help="Create the batch exams in this folder",
)
@click.option(
    "--clean",
    "-c",
    is_flag=True,
    default=False,
    help="Clean all latex compilation auxiliary files",
)
def main(
    paths: Path,
    questions_per_folder: list,
    batch_size: int,
    tex_path: Path,
    out_folder: Path,
    clean: bool,
) -> None:
    """Run the main tasks of the script."""
    cfg = {"folders": paths}
    cfg = validate(Pool.get_schema(), cfg)
    pool = Pool(**cfg)

    header = Tex.load(tex_path)

    b = ExamBatch(N=batch_size, pool=pool, tex=header, n=questions_per_folder)

    b.make_batch()

    b.compile(clean=clean, path=out_folder)

    b.dump(out_folder / "exams.yaml")
