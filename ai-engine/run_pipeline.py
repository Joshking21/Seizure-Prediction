import argparse
import logging
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from src.dataset_builder import build_dataset, prepare_splits
from src.train import train_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--subjects", nargs="+", default=["chb01", "chb02"])
    p.add_argument("--mock", action="store_true")
    p.add_argument("--rebuild", action="store_true")
    p.add_argument("--no-train", dest="train", action="store_false")
    p.set_defaults(train=True)
    return p.parse_args()


def main():
    args = parse_args()

    X, y = build_dataset(
        subject_ids=args.subjects,
        use_mock=args.mock,
        force_rebuild=args.rebuild,
    )

    splits = prepare_splits(X, y, balance=True)

    if not args.train:
        return

    metrics = train_model(splits)
    logger.info(f"Accuracy: {metrics['accuracy']:.2f}%")
    logger.info(f"Sensitivity: {metrics['sensitivity']:.2f}%")
    logger.info(f"Specificity: {metrics['specificity']:.2f}%")


if __name__ == "__main__":
    main()
