"""Shared CLI utilities for randex scripts."""

import logging
import sys

import click


def setup_logging(verbose: int = 0, quiet: bool = False) -> None:
    """
    Set up logging configuration for the CLI.

    Parameters
    ----------
    verbose : int
        Verbosity level (0=INFO, 1=DEBUG, 2+ more verbose DEBUG)
    quiet : bool
        If True, only show warnings and errors
    """
    if quiet:
        level = logging.WARNING
    elif verbose >= 1:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Create formatter
    formatter = logging.Formatter(fmt="%(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Set up the root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # For verbose mode, also show logger names and levels
    if verbose >= 2:
        formatter = logging.Formatter(
            fmt="[%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance.

    Parameters
    ----------
    name : str, optional
        Logger name. If None, uses the calling module name.

    Returns
    -------
    logging.Logger
        Configured logger instance
    """
    if name is None:
        # Get the calling module name
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "randex")
        else:
            name = "randex"

    return logging.getLogger(name)


class CustomCommand(click.Command):
    """Custom Click command that provides better error messages."""

    def parse_args(
        self,
        ctx: click.Context,
        args: list[str],
    ) -> list[str]:
        """
        Override parse_args to catch parameter parsing errors.

        This is a workaround to catch the error when the user passes multiple
        folder arguments to the command.

        Parameters
        ----------
        ctx : click.Context
            The click context.
        args : list[str]
            The arguments passed to the command.

        Returns
        -------
        list[str]:
            The remaining unparsed arguments.

        Examples
        --------
        ```bash
        exams examples/en/folder_* -t template.yaml -n 2
        ```
        """
        try:
            return super().parse_args(ctx, args)
        except click.UsageError as e:
            if "Got unexpected extra arguments" in str(e):
                # Extract the extra arguments from the error message
                error_msg = str(e)
                if "(" in error_msg and ")" in error_msg:
                    extra_args = error_msg.split("(")[1].split(")")[0]

                    raise click.UsageError(
                        f"❌ Multiple folder arguments detected: {extra_args}\n\n"
                        f"💡 This usually happens when your shell expands a glob pattern like 'examples/en/folder_*'\n"  # noqa: E501
                        f"   into multiple folder names before passing them to the command.\n\n"  # noqa: E501
                        f"🔧 Solutions:\n"
                        f'   • Put quotes around your glob pattern: "examples/en/folder_*"\n'  # noqa: E501
                        f"   • Or specify a single folder path instead of a glob pattern\n\n"  # noqa: E501
                        f'Example: exams "examples/en/folder_*" -t template.yaml -n 2'
                    ) from e
            raise
