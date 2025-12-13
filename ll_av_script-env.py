#!/usr/bin/env python3
"""
ll_av_script - Audio/Video Processing Script
Main entry point for the refactored application
"""

import sys
from ll_av_script.core.models import ProcessingConfig
from ll_av_script.cli import Application, create_argument_parser

PROG_VERSION = "2.0.0"


def main():
    """Main entry point"""
    print(f"ll_av_script v.{PROG_VERSION}")

    # Parse arguments
    parser = create_argument_parser(PROG_VERSION)
    args = parser.parse_args()

    # Create configuration
    config = ProcessingConfig(
        quiet_output=args.verbose,
        streamable=args.streamable,
        extract_aif=args.extract_aif,
        extract_m4a=args.extract_m4a,
        only_audio=args.only_extract_audios,
        only_explode=args.explode_only,
        no_interact=args.no_interact,
        start_time=args.start_time,
        end_time=args.end_time,
        filename=args.filename,
        edit_segments=args.edit,
    )

    # Run application
    app = Application(config)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())