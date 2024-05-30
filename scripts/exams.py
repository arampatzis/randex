"""Script that creates a batch of randomized exams."""
from pathlib import Path

import click

from randex.exam import Pool, Exam, ExamBatch, Header
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
    "--header-path",
    "-h",
    type=Path,
    help="Path to the yaml file that contains the header information",
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
    help="Clean all latex compilation auxiliary files"
)
def main(
    paths: Path,
    batch_size: int,
    header_path: Path,
    out_folder: Path,
    clean: bool,
) -> None:
    """Run the main tasks of the script."""
    
    cfg = {'folders': paths}
    cfg = validate(Pool.get_schema(), cfg)
    pool = Pool(**cfg)
        
    header = Header.load(header_path)
    
    b = ExamBatch(N=batch_size, pool=pool, header=header)
    b.make_batch()

    # b = ExamBatch.load(out_folder / 'exams.yaml')

    b.compile(clean=clean, path=out_folder)
    
    b.dump(out_folder / 'exams.yaml')
    