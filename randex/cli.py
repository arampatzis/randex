"""Shared CLI utilities for randex scripts."""

import click


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
