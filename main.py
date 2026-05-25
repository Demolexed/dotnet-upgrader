import sys
import logging
import argparse
from pathlib import Path

from config import load_config
from services.logger import setup_logging
from services.qualification import check_qualifications
from services.csproj import upgrade_all_csproj
from services.cs_files import process_all_cs_files
from services.yaml_files import process_all_yaml_files
from services.dockerfile import process_all_dockerfiles
from services.commit_message import write_commit_message


def parse_args():
    parser = argparse.ArgumentParser(description='Migrate a .NET repository to a target framework version')
    parser.add_argument('--repo-path', required=True, help='Path to the .NET repository')
    parser.add_argument('--config', default='upgrader-config.yml', help='Path to config file')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARN', 'ERROR'])
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(args.log_level)

    logger = logging.getLogger(__name__)
    config = load_config(args.config)

    repo_path = Path(args.repo_path)
    if not repo_path.is_dir():
        logger.error("Repository not found: %s", repo_path)
        sys.exit(1)

    qualifications = config.get('required-qualifications') or []
    if not check_qualifications(repo_path, qualifications, config):
        logger.error("Repository does not meet required qualifications")
        sys.exit(1)

    upgrade_report    = upgrade_all_csproj(repo_path, config)
    cs_report         = process_all_cs_files(repo_path, config)
    yaml_report       = process_all_yaml_files(repo_path, config)
    dockerfile_report = process_all_dockerfiles(repo_path, config)

    total_changes = (
        upgrade_report['changes']
        + cs_report['changes']
        + yaml_report['changes']
        + dockerfile_report['changes']
    )

    if total_changes == 0:
        logger.info("No changes applied")
        sys.exit(0)

    write_commit_message(config, upgrade_report['upgraded_files'], repo_path)
    logger.info("Done. Total changes: %d", total_changes)


if __name__ == '__main__':
    main()
