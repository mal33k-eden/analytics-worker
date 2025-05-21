import argparse
import logging

from app.pipeline.celery_config import celery_app


def create_arg_parser():
    parser = argparse.ArgumentParser(description='Start a Celery Worker')
    parser.add_argument('--loglevel', default='DEBUG', help='Logging level to use')
    parser.add_argument('--mingle-enabled', action='store_true', help='Enable worker state synchronization at startup')
    return parser


def main():
    parser = create_arg_parser()
    args = parser.parse_args()
    command = ['worker', f'--loglevel={args.loglevel}']
    if not args.mingle_enabled:
        command.append('--without-mingle')
    celery_app.worker_main(command)


if __name__ == '__main__':
    try:
        main()
    except ImportError as e:
        logging.error(f"Cannot import required modules: {e}")
        exit(1)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        exit(1)

# if __name__ == '__main__':
#     celery_app.worker_main(['worker', '--loglevel=DEBUG'])
