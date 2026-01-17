from .aws import use_aws_cloud
from .colab import release_colab_drive, use_colab_drive
from .gcs import use_gcs_cloud
from .gdrive import use_google_drive
from .kaggle import use_kaggle_dataset
from .local import use_local_drive
from .ncei import use_ncei_archive

__all__ = [
    "release_colab_drive",
    "use_aws_cloud",
    "use_colab_drive",
    "use_gcs_cloud",
    "use_google_drive",
    "use_kaggle_dataset",
    "use_local_drive",
    "use_ncei_archive",
]
