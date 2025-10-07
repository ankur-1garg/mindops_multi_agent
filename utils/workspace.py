# utils/workspace.py
import os
import stat
import subprocess
import tempfile
import shutil
from .logger import setup_logger

logger = setup_logger(__name__)


def setup_temporary_workspace(repo_url: str) -> str:
    """
    Creates a temporary directory and clones the specified Git repository into it.
    Returns the path to the temporary directory.
    """
    try:
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary workspace at: {temp_dir}")

        subprocess.run(
            ["git", "clone", repo_url, temp_dir],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Successfully cloned {repo_url} into workspace.")
        return temp_dir
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {e.stderr}")
        # Clean up the directory if cloning fails
        shutil.rmtree(temp_dir)
        raise
    except Exception as e:
        logger.error(f"An error occurred during workspace setup: {e}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise


def cleanup_workspace(temp_dir: str):
    """
    Recursively deletes the specified temporary directory.
    Handles Windows-specific permission issues with .git directories.
    """
    if not os.path.exists(temp_dir):
        return

    def handle_error(func, path, exc_info):
        """
        Error handler for shutil.rmtree that handles permission errors
        """
        import stat
        if not os.access(path, os.W_OK):
            # Change file permissions if needed
            os.chmod(path, stat.S_IWUSR)
            func(path)  # Try again
        else:
            raise  # If it's not a permission error, raise the exception

    try:
        # Try to remove read-only flag from .git directory first
        git_dir = os.path.join(temp_dir, '.git')
        if os.path.exists(git_dir):
            for root, dirs, files in os.walk(git_dir):
                for dir in dirs:
                    os.chmod(os.path.join(root, dir), stat.S_IRWXU)
                for file in files:
                    os.chmod(os.path.join(root, file), stat.S_IRWXU)

        # Remove the directory with error handler
        shutil.rmtree(temp_dir, onerror=handle_error)
        logger.info(f"Successfully cleaned up temporary workspace: {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to clean up workspace {temp_dir}: {e}")
        # Don't raise the exception as this is cleanup code
